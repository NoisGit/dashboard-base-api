"""Whitelist-related Pydantic schemas for the Sentinel Enterprise API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from .base_schemas import BaseResponse


class WhitelistCreateRequest(BaseModel):
    """Schema for creating a whitelist authorization."""
    id_number: str
    full_name: str
    reason: Optional[str] = None
    expiration_date: Optional[datetime] = None


class WhitelistResponse(BaseResponse):
    """Schema for whitelist response."""
    id: int
    company_id: int
    location_id: Optional[int] = None
    external_people_id: Optional[int] = None
    id_number: str
    full_name: str
    reason: Optional[str] = None
    expiration_date: Optional[datetime] = None
    created_at: Optional[datetime] = None


class WhitelistCheckRequest(BaseModel):
    """Schema for checking whitelist access."""
    id_number: str


class WhitelistCheckResponse(BaseModel):
    """Schema for whitelist check response."""
    company_id: int
    location_id: int
    external_people_id: Optional[int] = None
    id_number: str
    full_name: Optional[str] = None
    status: str
    message: str
    reason: Optional[str] = None
    expiration_date: Optional[datetime] = None


__all__ = [
    "WhitelistCreateRequest",
    "WhitelistResponse",
    "WhitelistCheckRequest",
    "WhitelistCheckResponse",
]
