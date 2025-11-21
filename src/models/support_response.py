from __future__ import annotations

"""
Support response database model for the Sentinel Enterprise API.

Represents an individual response to a support ticket, including:
- The parent ticket (ticket_id)
- The comment/answer text
- Optional media URL
- Who created the response and when
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .support_ticket import SupportTicket
    from .user import User


class SupportResponse(SQLModel, table=True):
    __tablename__ = "support_response"

    id: Optional[int] = Field(default=None, primary_key=True)

    # FK to support_ticket.id
    ticket_id: int = Field(foreign_key="support_ticket.id")

    comment: Optional[str] = Field(default=None, max_length=500)
    media_url: Optional[str] = Field(default=None, max_length=255)

    # Audit fields
    created_by: Optional[int] = Field(
        default=None,
        foreign_key="users.id",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    ticket: "SupportTicket" = Relationship(back_populates="responses")
    creator: Optional["User"] = Relationship(
        back_populates="support_responses_created",
    )
