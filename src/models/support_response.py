from __future__ import annotations

"""
Support response database model for the Sentinel Enterprise API.

Represents an individual response to a support ticket, including:
- The parent ticket (ticket_id)
- The comment/answer text
- Optional media name
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

    # FK to support_ticket.id (DBML: ticket_id)
    ticket_id: int = Field(foreign_key="support_ticket.id")

    # DBML: comment text(500) (no [null] → obligatorio)
    comment: str = Field(max_length=500)

    # DBML: media_name varchar(255) [null]
    media_name: Optional[str] = Field(default=None, max_length=255)

    # Audit fields (DBML: created_by int, created_at timestamp)
    created_by: int = Field(
        foreign_key="users.id",
    )
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    ticket: "SupportTicket" = Relationship(back_populates="responses")
    creator: Optional["User"] = Relationship(
        back_populates="support_responses_created",
    )
