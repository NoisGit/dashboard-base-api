from __future__ import annotations

"""
Support ticket database model for the Sentinel Enterprise API.

Represents a support request opened by a user, including:
- Title and detailed comment
- Optional media URL (screenshot, video, etc.)
- Status flag (open/closed or active/inactive)
- Who created the ticket and when
- Related responses from the support team
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .support_response import SupportResponse
    from .user import User


class SupportTicket(SQLModel, table=True):
    __tablename__ = "support_ticket"

    id: Optional[int] = Field(default=None, primary_key=True)

    title: str = Field(max_length=50)
    comment: Optional[str] = Field(default=None, max_length=500)
    media_url: Optional[str] = Field(default=None, max_length=255)

    status: bool = Field(default=True)

    created_by: Optional[int] = Field(
        default=None,
        foreign_key="users.id",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    responses: List["SupportResponse"] = Relationship(
        back_populates="ticket",
    )
    creator: Optional["User"] = Relationship(
        back_populates="support_tickets_created",
    )
