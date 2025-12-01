"""User-related Pydantic schemas for the Sentinel Enterprise API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserCreateRequest(BaseModel):
    """Schema for creating a user."""
    username: str
    full_name: str
    email: EmailStr
    password: str  # plain text, will be hashed with Argon2 in the service
    role: str      # "admin", "superadmin", "janitor", "subadmin", "client"
    plan_id: int
    status: bool = True


class UserUpdateRequest(BaseModel):
    """Schema for updating a user profile."""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    status: Optional[bool] = None


class UserResponse(BaseModel):
    """Schema for user response (without sensitive data)."""
    id: int
    username: str
    full_name: str
    email: EmailStr
    role: str
    status: bool
    is_active: bool
    plan_id: int
    created_at: Optional[datetime] = None

    class Config:
        """Pydantic config to allow ORM objects."""
        from_attributes = True


__all__ = [
    "UserCreateRequest",
    "UserUpdateRequest",
    "UserResponse",
]
