"""Location-related Pydantic schemas for the Locentr API."""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

from .base_schemas import BaseResponse


class LocationCreateRequest(BaseModel):
    """Schema for creating a location"""
    name: str = Field(min_length=2, max_length=120)
    address: str = Field(min_length=3, max_length=255)
    country: Optional[str] = Field(default=None, max_length=80)
    logo: Optional[str] = Field(default=None, max_length=255)


class LocationUpdateRequest(BaseModel):
    """Schema for updating a location"""
    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    address: Optional[str] = Field(default=None, min_length=3, max_length=255)
    country: Optional[str] = Field(default=None, max_length=80)
    logo: Optional[str] = Field(default=None, max_length=255)


class LocationResponse(BaseResponse):
    """Schema for location response"""
    id: int
    name: str
    address: str
    country: Optional[str] = None
    logo: Optional[str] = None
    company_ids: list[int] = Field(default_factory=list)
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


class AccessListResponse(BaseResponse):
    """Schema for Access List response."""
    id: int
    location_id: int
    id_number: str
    full_name: str
    type_access_list: str
    reason: Optional[str] = None
    vehicle_plate: Optional[str] = None
    expiration_date: Optional[datetime] = None
    created_at: Optional[datetime] = None


class AccessListResponseList(BaseModel):
    items: List[AccessListResponse]


__all__ = [
    "LocationCreateRequest",
    "LocationUpdateRequest",
    "LocationResponse",
    "LocationAssignCompanyRequest",
    "LocationAssignUserRequest",
    "LocationUserAssignmentResponse",
    "AccessListResponse",
]
