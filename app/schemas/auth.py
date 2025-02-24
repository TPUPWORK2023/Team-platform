from pydantic import BaseModel

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    id_token: str
    refresh_token: str
    expires_in: int