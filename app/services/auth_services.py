import requests
import os
from fastapi import HTTPException

class AuthService:
    def __init__(self):
        self.firebase_auth_url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
        self.api_key = os.getenv("FIREBASE_API_KEY")  # Get from your Firebase project settings

    async def login_user(self, email: str, password: str):
        """
        Login with email and password to get Firebase tokens.
        
        Args:
            email (str): Email of the user
            password (str): Password of the user
        
        Returns:
            dict: Firebase tokens and expiry
        
        Raises:
            HTTPException: If login fails
            HTTPException: If there is an error with the request
        """
        try:
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            
            response = requests.post(
                f"{self.firebase_auth_url}?key={self.api_key}",
                json=payload
            )
            
            if response.status_code != 200:
                error_message = response.json().get("error", {}).get("message", "Login failed")
                raise HTTPException(status_code=401, detail=error_message)
                
            data = response.json()
            return {
                "id_token": data["idToken"],
                "refresh_token": data["refreshToken"],
                "expires_in": data["expiresIn"]
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))