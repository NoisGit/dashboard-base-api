"""User-related Pydantic schemas for the Sentinel Enterprise API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from src.core.enums import UserRole
from .base_schemas import BaseResponse


class UserCreateRequest(BaseModel):
    """Schema for creating a user."""
    username: str
    full_name: str
    email: EmailStr
    password: str  # plain text, will be hashed in the service
    role: UserRole
    plan_id: int
    status: bool = True


class UserUpdateRequest(BaseModel):
    """Schema for updating a user."""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    status: Optional[bool] = None


class UserResponse(BaseResponse):
    """Schema for user response (without sensitive data)."""
    id: int
    username: str
    full_name: str
    email: EmailStr
    role: UserRole
    status: bool
    is_active: bool
    plan_id: int
    created_at: Optional[datetime] = None


__all__ = [
    "UserCreateRequest",
    "UserUpdateRequest",
    "UserResponse",
]
