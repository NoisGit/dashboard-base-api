"""Blacklist-related Pydantic schemas for the Sentinel Enterprise API."""

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
    location_id: int
    id_number: str
    full_name: str
    reason: str
    created_at: Optional[datetime] = None


__all__ = [
    "BlacklistCreateRequest",
    "BlacklistResponse",
]
