"""Emergency contact-related Pydantic schemas for the Coredeck API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from .base_schemas import BaseResponse


class EmergencyContactCreateRequest(BaseModel):
    """Schema for creating an emergency contact."""
    name: str
    phone: str
    location_id: Optional[int] = None
    is_default: bool = False


class EmergencyContactUpdateRequest(BaseModel):
    """Schema for updating an emergency contact."""
    name: Optional[str] = None
    phone: Optional[str] = None
    location_id: Optional[int] = None
    is_default: Optional[bool] = None


class EmergencyContactResponse(BaseResponse):
    """Schema for emergency contact response."""
    id: int
    name: str
    phone: str
    location_id: Optional[int] = None
    is_default: bool
    created_by: int
    created_at: Optional[datetime] = None


__all__ = [
    "EmergencyContactCreateRequest",
    "EmergencyContactUpdateRequest",
    "EmergencyContactResponse",
]
