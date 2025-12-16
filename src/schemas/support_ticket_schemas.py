"""Support ticket Pydantic schemas for the Sentinel Enterprise API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from src.core.enums import SupportTicketStatus
from .base_schemas import BaseResponse


class SupportTicketCreateRequest(BaseModel):
    """Schema for creating a support ticket"""
    title: str
    description: str
    media_name: Optional[str] = None


class SupportTicketUpdateRequest(BaseModel):
    """Schema for updating a support ticket"""
    title: Optional[str] = None
    description: Optional[str] = None
    media_name: Optional[str] = None
    status: Optional[SupportTicketStatus] = None


class SupportTicketResponse(BaseResponse):
    """Schema for support ticket response"""
    id: int
    title: str
    description: str
    media_name: Optional[str] = None
    status: SupportTicketStatus
    created_by: int
    created_at: datetime
