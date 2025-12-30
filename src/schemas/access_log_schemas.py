"""Access Log schemas for Sentinel Enterprise API."""

from datetime import datetime
from typing import Optional, List, Any

from pydantic import BaseModel, Field


# =============================================================================
# Request Schemas
# =============================================================================

class AccessLogCreateRequest(BaseModel):
    """Request schema for creating an access log entry."""
    location_id: int
    external_people_id: int
    type_document: Optional[str] = Field(default=None, max_length=30)
    vehicle_plate: Optional[str] = Field(default=None, max_length=20)
    office: Optional[str] = Field(default=None, max_length=20)
    comment: Optional[str] = Field(default=None, max_length=100)

    # Dynamic form responses (simple format from frontend)
    # [{field_id: int, value: str | List[str]}]
    custom_form_responses: Optional[List[dict]] = None

    # Entry images (list of image names uploaded to Azure)
    entry_images: Optional[List[str]] = None


class AccessLogExitRequest(BaseModel):
    """Request schema for registering an exit."""
    exit_comment: Optional[str] = Field(default=None, max_length=100)

    # Exit images (list of image names uploaded to Azure)
    exit_images: Optional[List[str]] = None


# =============================================================================
# Response Schemas
# =============================================================================


class ExternalPeopleResponse(BaseModel):
    """Response schema for external people in access log."""
    id: int
    name: str
    id_number: str
    gender: Optional[str] = None
    file_name: Optional[str] = None


class LocationResponse(BaseModel):
    """Response schema for location in access log."""
    id: int
    name: str
    address: Optional[str] = None


class AccessLogResponse(BaseModel):
    """Response schema for access log."""
    id: int
    location_id: int
    external_people_id: int

    # Access information
    type_document: Optional[str] = None
    vehicle_plate: Optional[str] = None
    office: Optional[str] = None
    comment: Optional[str] = None

    # Exit information
    exit_date: Optional[datetime] = None
    exit_comment: Optional[str] = None
    exit_created_by: Optional[int] = None

    # Audit
    created_by: int
    created_at: datetime

    # Dynamic form responses (JSONB snapshot)
    custom_form_responses: Optional[Any] = None

    # Relationships
    external_people: Optional[ExternalPeopleResponse] = None
    location: Optional[LocationResponse] = None
    images: List[str] = []


class AccessLogListResponse(BaseModel):
    """Simplified response for listing access logs."""
    id: int
    location_id: int
    external_people_id: int
    vehicle_plate: Optional[str] = None
    office: Optional[str] = None
    exit_date: Optional[datetime] = None
    created_at: datetime

    # Only essential relationship data
    external_people: Optional[ExternalPeopleResponse] = None
    images: List[str] = []
