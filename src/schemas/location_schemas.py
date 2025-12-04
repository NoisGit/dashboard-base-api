"""Location-related Pydantic schemas for the Sentinel Enterprise API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class LocationCreateRequest(BaseModel):
    """Schema for creating a location (portería)."""

    name: str
    address: str
    country: Optional[str] = None
    logo: Optional[str] = None


class LocationUpdateRequest(BaseModel):
    """Schema for updating a location (portería)."""

    name: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    logo: Optional[str] = None


class LocationResponse(BaseModel):
    """Schema for location response (without internal details)."""

    id: int
    name: str
    address: str
    country: Optional[str] = None
    logo: Optional[str] = None
    company_id: Optional[int] = None
    is_active: bool
    created_by: int
    created_at: Optional[datetime] = None

    class Config:
        """Pydantic config to allow ORM objects."""
        from_attributes = True


class LocationAssignCompanyRequest(BaseModel):
    """Payload to assign a location to a company."""

    company_id: int


class LocationAssignUserRequest(BaseModel):
    """Payload to assign a user (janitor/porter) to a location."""

    user_id: int


class LocationUserAssignmentResponse(BaseModel):
    """Response for a user–location assignment."""

    id: int
    location_id: int
    user_id: int
    created_by: int
    created_at: datetime

    class Config:
        """Pydantic config to allow ORM objects."""
        from_attributes = True


__all__ = [
    "LocationCreateRequest",
    "LocationUpdateRequest",
    "LocationResponse",
    "LocationAssignCompanyRequest",
    "LocationAssignUserRequest",
    "LocationUserAssignmentResponse",
]
