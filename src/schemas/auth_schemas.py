"""User-related Pydantic schemas for the Coredeck API."""

from pydantic import BaseModel, EmailStr


class AuthRecoveryPasswordRequest(BaseModel):
    """Schema for user recovery password"""
    email: EmailStr


class AuthResetPasswordRequest(BaseModel):
    """Schema for user recovery password"""
    reset_token: str
    new_password: str
    confirm_new_password: str


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str


class AuthTokenResponse(BaseModel):
    """Schema for user token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    """Schema for access token only response"""
    access_token: str
    token_type: str = "bearer"


__all__ = [
    "AuthRecoveryPasswordRequest",
    "AuthResetPasswordRequest",
    "RefreshTokenRequest",
    "AuthTokenResponse",
    "AccessTokenResponse",
]
