"""User-related Pydantic schemas for the Locentr API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from src.core.enums import UserRole
from .base_schemas import BaseResponse


class UserCreateRequest(BaseModel):
    """Schema for creating a user"""
    username: str = Field(min_length=2, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")
    full_name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole
    plan_id: Optional[int] = None
    status: bool = True


class UserUpdateRequest(BaseModel):
    """Schema for updating a user"""
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=160)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    status: Optional[bool] = None


class UserSuspendRequest(BaseModel):
    """Schema for suspending a user"""
    reason_suspension: Optional[str] = None


class UserLoginRequest(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class OperatorLoginRequest(BaseModel):
    """Schema for operator login"""
    username: str
    password: str = Field(min_length=1, max_length=128)


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str = Field(min_length=20, max_length=4096)


class UserChangePasswordRequest(BaseModel):
    """Schema for changing user password"""
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)
    confirm_new_password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseResponse):
    """Schema for user response (without sensitive data)"""
    id: int
    username: str
    full_name: str
    email: EmailStr
    role: UserRole
    status: bool
    is_active: bool
    plan_id: Optional[int] = None
    created_at: Optional[datetime] = None


class OperatorResponse(BaseResponse):
    """Schema for operator response (without sensitive data)"""
    id: int
    username: str
    full_name: str
    email: EmailStr
    status: bool
    created_at: Optional[datetime] = None


class UserMeResponse(BaseModel):
    """Schema for current user profile (/auth/me)"""
    id: int
    full_name: str
    email: EmailStr
    role: UserRole
    company_id: Optional[int] = None
    avatar: Optional[str] = None


class UserTokenResponse(BaseModel):
    """Schema for user token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    """Schema for access token only response"""
    access_token: str
    token_type: str = "bearer"
