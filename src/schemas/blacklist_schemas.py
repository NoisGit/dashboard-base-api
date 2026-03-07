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
    company_id: int
    location_id: Optional[int] = None
    external_people_id: Optional[int] = None
    id_number: str
    full_name: str
    reason: str
    created_at: Optional[datetime] = None


class BlacklistCheckRequest(BaseModel):
    """Schema for checking blacklist access."""
    id_number: str


class BlacklistCheckResponse(BaseModel):
    """Schema for blacklist check response."""
    company_id: int
    location_id: int
    external_people_id: Optional[int] = None
    id_number: str
    full_name: Optional[str] = None
    status: str
    message: str
    reason: Optional[str] = None


__all__ = [
    "BlacklistCreateRequest",
    "BlacklistResponse",
    "BlacklistCheckRequest",
    "BlacklistCheckResponse",
]
