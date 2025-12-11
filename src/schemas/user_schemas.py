"""User-related Pydantic schemas for the Sentinel Enterprise API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from src.core.enums import UserRole
from .base_schemas import BaseResponse


class UserCreateRequest(BaseModel):
    """Schema for creating a user"""
    username: str
    full_name: str
    email: EmailStr
    password: str
    role: UserRole
    plan_id: int
    status: bool = True


class UserUpdateRequest(BaseModel):
    """Schema for updating a user"""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    status: Optional[bool] = None


class UserLoginRequest(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str


class UserResponse(BaseResponse):
    """Schema for user response (without sensitive data)"""
    id: int
    username: str
    full_name: str
    email: EmailStr
    role: UserRole
    status: bool
    is_active: bool
    plan_id: int
    created_at: Optional[datetime] = None


class UserTokenResponse(BaseModel):
    """Schema for user token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    """Schema for access token only response"""
    access_token: str
    token_type: str = "bearer"


__all__ = [
    "UserCreateRequest",
    "UserUpdateRequest",
    "UserResponse",
    "UserLoginRequest",
    "UserTokenResponse",
    "RefreshTokenRequest",
    "AccessTokenResponse",
]
