from fastapi import APIRouter, Depends, HTTPException
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth_services import AuthService

router = APIRouter()
auth_service = AuthService()

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login with email and password to get Firebase tokens.
    
    Args:
        request (LoginRequest): The login credentials
        
    Returns:
        LoginResponse: Firebase tokens and expiry
        
    Raises:
        HTTPException: If login fails
    """
    try:
        result = await auth_service.login_user(
            email=request.email,
            password=request.password
        )
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        status_code = getattr(e, 'status_code', 500)
        raise HTTPException(status_code=status_code, detail=str(e))