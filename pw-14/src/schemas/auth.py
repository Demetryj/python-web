"""Pydantic schemas for authentication requests and responses."""

from pydantic import BaseModel, EmailStr


class TokenSchema(BaseModel):
    """Token response returned after successful authentication or refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    
    
class RequestEmail(BaseModel):
    """Request payload containing a user email address."""

    email: EmailStr
    

class ResetPasswordSchema(BaseModel):
    """Request payload for confirming a password reset."""

    token: str
    password: str
