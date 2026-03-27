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
    plan_id: Optional[int] = None
    status: bool = True


class UserUpdateRequest(BaseModel):
    """Schema for updating a user"""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    status: Optional[bool] = None


class UserSuspendRequest(BaseModel):
    """Schema for suspending a user"""
    reason_suspension: Optional[str] = None


class UserLoginRequest(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class JanitorLoginRequest(BaseModel):
    """Schema for janitor login"""
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str


class UserChangePasswordRequest(BaseModel):
    """Schema for changing user password"""
    current_password: str
    new_password: str
    confirm_new_password: str


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


class JanitorResponse(BaseResponse):
    """Schema for janitor response (without sensitive data)"""
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
