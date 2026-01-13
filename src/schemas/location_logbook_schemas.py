"""Location logbook schemas for Sentinel Enterprise API."""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class LocationLogbookCreateRequest(BaseModel):
    """Request schema for creating a location logbook entry."""
    location_id: int
    description: str = Field(min_length=1, max_length=1000)

    # Media uploaded to Azure (store blob name)
    media_name: Optional[str] = Field(default=None, max_length=255)
    media_type: Optional[str] = Field(default=None, max_length=20)


class LocationLogbookResponse(BaseModel):
    """Response schema for a location logbook entry."""
    id: int
    location_id: int
    created_by: int
    description: str

    media_url: Optional[str] = None
    media_type: Optional[str] = None

    created_at: datetime

    location_name: Optional[str] = None
    location_address: Optional[str] = None
    user_full_name: Optional[str] = None


class AuthorityLinkResponse(BaseModel):
    """Response schema for authority access link (QR target)."""
    relative_path: str


class AuthorityViewResponse(BaseModel):
    """Response schema for authority view."""
    location_name: str
    entries: List[LocationLogbookResponse]
