"""Authentication Pydantic schemas."""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from fastapi_users import schemas


class UserRead(schemas.BaseUser[int]):
    """Schema for reading user data."""
    username: str
    email: EmailStr


class UserCreate(schemas.BaseUserCreate):
    """Schema for user registration."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    turnstile_token: str = Field(..., description="Cloudflare Turnstile token")


class UserUpdate(schemas.BaseUserUpdate):
    """Schema for updating user data."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)


class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str


class LoginRequest(BaseModel):
    """Schema for login request."""
    username: str = Field(..., description="Username or email")
    password: str
    turnstile_token: str = Field(..., description="Cloudflare Turnstile token")
