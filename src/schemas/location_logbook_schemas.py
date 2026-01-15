"""Location logbook schemas for Sentinel Enterprise API."""

from datetime import datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field


class LocationLogbookMediaType(str, Enum):
    """Allowed media types for logbook entries."""
    PHOTO = "PHOTO"
    VIDEO = "VIDEO"


class LocationLogbookCreateRequest(BaseModel):
    """Request schema for creating a location logbook entry."""
    location_id: int
    description: str = Field(min_length=1, max_length=1000)

    media_name: Optional[str] = Field(default=None, max_length=255)
    media_type: Optional[LocationLogbookMediaType] = None


class LocationLogbookResponse(BaseModel):
    """Response schema for a location logbook entry."""
    id: int
    location_id: int
    created_by: int
    description: str

    media_url: Optional[str] = None
    media_type: Optional[LocationLogbookMediaType] = None

    created_at: datetime

    location_name: Optional[str] = None
    location_address: Optional[str] = None
    user_full_name: Optional[str] = None


class LocationLogbookSettingsUpdateRequest(BaseModel):
    """Request schema for enabling/disabling location logbook feature."""
    enabled: bool


class LocationLogbookSettingsResponse(BaseModel):
    """Response schema for location logbook settings."""
    location_id: int
    is_enabled: bool
    updated_by: Optional[int] = None
    updated_at: Optional[datetime] = None


class PoliceAccessCreateRequest(BaseModel):
    """Request schema for creating a police access link (QR target)."""
    location_id: int


class PoliceLinkResponse(BaseModel):
    """Response schema for police access link (QR target)."""
    relative_path: str
    expires_at: datetime


class PoliceViewResponse(BaseModel):
    """Response schema for police view."""
    location_name: str
    entries: List[LocationLogbookResponse]
