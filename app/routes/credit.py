from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any
from app.schemas.credit import CreditsRequestSchema, InvalidateCreditRequestSchema, CreditsResponseSchema
from app.services.credit import get_manager_team_size, apply_discount, update_credit_data, get_credits, invalidate_credit
from app.services.team import is_valid_email
from app.dependencies.auth_dependencies import verify_token
import stripe
from app.config import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_KEY
import os

# initialize_app(cred)
router = APIRouter()
stripe.api_key = STRIPE_SECRET_KEY


@router.post("/buy_credits", response_model=Dict[str, str])
async def buy_credits_route(request: CreditsRequestSchema, manager: dict = Depends(verify_token)) -> Dict[str, str]:
    """
    Process credit purchase using Stripe Checkout with dynamic quantity and discount.

    Parameters:
        request (CreditsRequestSchema): The request containing the number of credits to buy.
        manager (dict): The manager's information obtained from the token.

    Raises:
        HTTPException: If the manager's email is not provided or if there is a Stripe error.

    Returns:
        Dict[str, str]: A dictionary containing the checkout URL.
    """
    manager_email = manager.get('email')
    if not manager_email:
        raise HTTPException(status_code=400, detail="Manager email is required.")

    # Get active team member count
    try:
        team_size = await get_manager_team_size(manager_email)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving team size: {str(e)}")

    # Calculate discount and final price
    try:
        discount = apply_discount(team_size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating price: {str(e)}")

    # Create Stripe Checkout session
    price_per_credit = os.environ.get("BASE_PRICE_PER_CREDIT")
    if not price_per_credit or not price_per_credit.replace(".", "", 1).isdigit():
        raise ValueError(f"Invalid BASE_PRICE_PER_CREDIT: {price_per_credit}")

    price_per_credit = float(price_per_credit)

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            metadata={
                "manager_email": manager_email,
                "credits": request.credits,
            }, 
            line_items=[{
                "price_data": {
                    "currency": "inr",
                    "product_data": {"name": "Credits Purchase"},
                    "unit_amount": int(price_per_credit * (1 - discount) * 100), 
                },
                "quantity": request.credits,
            }],
            mode="payment",
            success_url="https://google.com",
            cancel_url="https://facebook.com",
        )
    except stripe.error.StripeError as e:
        status_code = getattr(e, 'status_code', 500)
        raise HTTPException(status_code=status_code, detail=f"Stripe error: {str(e)}")
    except Exception as e:
        status_code = getattr(e, 'status_code', 500)
        raise HTTPException(status_code=status_code, detail=f"Unexpected error: {str(e)}")

    return {"checkout_url": session.url}


@router.post("/webhook")
async def stripe_webhook(request: Request) -> Dict[str, Any]:
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    try:
        event = stripe.Webhook.construct_event(
            payload,  # Ensure proper decoding
            sig_header,
            STRIPE_WEBHOOK_KEY
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload format")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature. Check STRIPE_WEBHOOK_KEY.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {str(e)}")

    # Process successful payment
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        manager_email = session["metadata"].get("manager_email")
        credits = int(session["metadata"].get("credits", 0))

        try:
            await update_credit_data(manager_email, credits)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating credit data: {str(e)}")

        return {"status": "success", "message": "Credits updated successfully"}

    return {"status": "ignored", "message": "Event not handled"}



@router.get("/get_credits", response_model=CreditsResponseSchema)
async def get_credits_route(manager: dict = Depends(verify_token)) -> CreditsResponseSchema:
    """
    Retrieve the current number of credits for a manager.

    Parameters:
        manager (dict): The manager's information obtained from the token.

    Raises:
        HTTPException: If there is an error retrieving credits.

    Returns:
        CreditsResponseSchema: A schema containing the current number of credits.
    """
    try:
        credits = await get_credits(manager['email'])
        return {"credits": credits}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        status_code = getattr(e, 'status_code', 500)
        raise HTTPException(status_code=status_code, detail=str(e))


@router.post("/invalidate_credit")
async def invalidate_credit_route(
    request: InvalidateCreditRequestSchema, 
    manager: dict = Depends(verify_token)
) -> Dict[str, Any]:
    """
    Invalidate a credit from a team member and restore it to the manager's pool.

    Parameters:
        request (InvalidateCreditRequestSchema): The request containing the team member's email.
        manager (dict): The manager's information obtained from the token.

    Raises:
        HTTPException: If there is an error invalidating the credit.

    Returns:
        Dict[str, Any]: A dictionary containing the result of the invalidation.
    """
    try:
        # Validate team member email
        if not request.team_member_email:
            raise HTTPException(status_code=400, detail="Team member email is required")
        
        if not is_valid_email(request.team_member_email):
            raise HTTPException(status_code=400, detail="Invalid email format")

        # Invalidate credit
        result = await invalidate_credit(request.team_member_email, manager['email'])
        return result

    except HTTPException as error:
        # Re-raising HTTPException to preserve the status code and detail
        raise error

    except Exception as e:
        # Handle unexpected errors
        status_code = getattr(e, 'status_code', 500)
        raise HTTPException(status_code=500, detail=str(e))