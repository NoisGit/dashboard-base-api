"""Blacklist-related Pydantic schemas for the Coredeck API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from .base_schemas import BaseResponse


class BlacklistCreateRequest(BaseModel):
    """Schema for creating a blacklist restriction."""
    id_number: str
    full_name: str
    reason: str


class BlacklistResponse(BaseResponse):
    """Schema for blacklist response."""
    id: int
    company_id: int
    location_id: Optional[int] = None
    external_people_id: Optional[int] = None
    id_number: str
    full_name: str
    reason: str
    created_at: Optional[datetime] = None


__all__ = [
    "BlacklistCreateRequest",
    "BlacklistResponse",
]
