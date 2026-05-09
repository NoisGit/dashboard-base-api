"""Service contact-related Pydantic schemas for the Coredeck API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from .base_schemas import BaseResponse


class ServiceContactCreateRequest(BaseModel):
    """Schema for creating a service contact."""
    service_name: str
    person_name: str
    email: str
    phone: str
    location_id: Optional[int] = None


class ServiceContactUpdateRequest(BaseModel):
    """Schema for updating a service contact."""
    service_name: Optional[str] = None
    person_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class ServiceContactResponse(BaseResponse):
    """Schema for service contact response."""
    id: int
    location_id: Optional[int] = None
    service_name: str
    person_name: str
    email: str
    phone: str
    created_by: int
    created_at: Optional[datetime] = None


__all__ = [
    "ServiceContactCreateRequest",
    "ServiceContactUpdateRequest",
    "ServiceContactResponse",
]
