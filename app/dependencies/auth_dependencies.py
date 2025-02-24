from fastapi import Header, HTTPException
from firebase_admin import auth, credentials, initialize_app
from app.config import FIREBASE_CREDENTIALS_PATH

# Initialize Firebase Admin SDK
cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
initialize_app(cred)

async def verify_token(authorization: str = Header(...)) -> dict:
    """Verifies Firebase ID Token from the Authorization header.

    Args:
        authorization (str): The Authorization header containing the Bearer token.

    Raises:
        HTTPException: If the authorization scheme is invalid or the token is invalid.

    Returns:
        dict: The decoded token if verification is successful.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    
    id_token = authorization.split("Bearer ")[1]
    
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
