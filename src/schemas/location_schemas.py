"""Location-related Pydantic schemas for the Sentinel Enterprise API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from .base_schemas import BaseResponse


class LocationCreateRequest(BaseModel):
    """Schema for creating a location"""
    name: str
    address: str
    country: Optional[str] = None
    logo: Optional[str] = None


class LocationUpdateRequest(BaseModel):
    """Schema for updating a location"""
    name: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    logo: Optional[str] = None


class LocationResponse(BaseResponse):
    """Schema for location response"""
    id: int
    name: str
    address: str
    country: Optional[str] = None
    logo: Optional[str] = None
    company_id: Optional[int] = None
    is_active: bool
    created_by: int
    created_at: Optional[datetime] = None


class LocationAssignCompanyRequest(BaseModel):
    """Payload to assign a location to a company."""
    company_id: int


class LocationAssignUserRequest(BaseModel):
    """Payload to assign a user to a location"""
    user_id: int


class LocationUserAssignmentResponse(BaseResponse):
    """Response for a user–location assignment."""
    id: int
    location_id: int
    user_id: int
    created_by: int
    created_at: datetime


__all__ = [
    "LocationCreateRequest",
    "LocationUpdateRequest",
    "LocationResponse",
    "LocationAssignCompanyRequest",
    "LocationAssignUserRequest",
    "LocationUserAssignmentResponse",
]
