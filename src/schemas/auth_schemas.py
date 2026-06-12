"""Authentication schemas for the Locentr API."""

from pydantic import BaseModel, EmailStr, Field


class AuthRecoveryPasswordRequest(BaseModel):
    """Schema for user recovery password"""
    email: EmailStr


class AuthResetPasswordRequest(BaseModel):
    """Schema for user recovery password"""
    reset_token: str = Field(min_length=20, max_length=255)
    new_password: str = Field(min_length=8, max_length=128)
    confirm_new_password: str = Field(min_length=8, max_length=128)


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str = Field(min_length=20, max_length=4096)


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
