"""Whitelist-related Pydantic schemas for the Sentinel Enterprise API."""

from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel

from .base_schemas import BaseResponse


class WhitelistCreateRequest(BaseModel):
    """Schema for creating a whitelist authorization."""
    id_number: str
    full_name: str
    reason: Optional[str] = None
    expiration_date: Optional[date] = None


class WhitelistResponse(BaseResponse):
    """Schema for whitelist response."""
    id: int
    location_id: int
    id_number: str
    full_name: str
    reason: Optional[str] = None
    expiration_date: Optional[date] = None
    created_at: Optional[datetime] = None


__all__ = [
    "WhitelistCreateRequest",
    "WhitelistResponse",
]
