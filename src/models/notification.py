"""
This module contains SQLModel classes for managing user notifications
within the enterprise system, including message delivery, read status,
and notification targeting.
"""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Notification(SQLModel, table=True):
    """
    Represents a notification sent to a user, including message content,
    read status, and sender information for communication tracking.
    """
    __tablename__ = "notifications"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: Optional[str] = Field(max_length=100, default=None)
    message: Optional[str] = Field(default=None)
    created_by_user_id: Optional[int] = Field(
        default=None, foreign_key="users.id")
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    read_at: Optional[datetime] = Field(default=None)
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
