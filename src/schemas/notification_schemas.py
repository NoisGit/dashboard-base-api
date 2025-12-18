"""Notification Schemas for Request and Response Models."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

# Request schemas


class SimpleNoticationRequest(BaseModel):
    """Schema for sending a simple notification with title and message."""
    title: str
    message: str


class NotificationResponse(BaseModel):
    """Schema for notification response indicating success and failure counts."""
    success: int
    failed: int

class NotificationMessageResponse(BaseModel):
    """Schema for individual notification message details."""
    id: int
    title: str
    message: str
    read_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
