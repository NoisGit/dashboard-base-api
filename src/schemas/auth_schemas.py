"""User-related Pydantic schemas for the Sentinel Enterprise API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from .base_schemas import BaseResponse


class AuthRecoveryPasswordRequest(BaseModel):
    """Schema for user recovery password"""
    email: EmailStr


class AuthResetPasswordRequest(BaseModel):
    """Schema for user recovery password"""
    reset_token: str
    new_password: str
    confirm_new_password: str


__all__ = [
    "AuthRecoveryPasswordRequest",
    "AuthResetPasswordRequest",
]
