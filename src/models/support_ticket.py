"""
Support ticket database model for the Locentr API.

Represents a support request opened by a user, including:
- Title and detailed description
- Optional media name (screenshot, video, etc.)
- Status value using a fixed set of states
- Who created the ticket and when
- Related responses from the support team
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

from src.core.enums import SupportTicketStatus

if TYPE_CHECKING:
    from .support_response import SupportResponse
    from .user import User


class SupportTicket(SQLModel, table=True):
    """Support ticket table"""

    __tablename__ = "support_ticket"

    id: Optional[int] = Field(default=None, primary_key=True)

    # DBML: title varchar(50)
    title: str = Field(max_length=50)

    # DBML: description text(1000)
    description: str = Field(max_length=1000)

    # DBML: media_name varchar(255) [null]
    media_name: Optional[str] = Field(default=None, max_length=255)

    # DBML: status varchar(20)
    status: SupportTicketStatus = Field(default=SupportTicketStatus.OPEN)

    # Audit fields (DBML: created_by int, created_at timestamp)
    created_by: int = Field(
        foreign_key="users.id",
    )
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    responses: List["SupportResponse"] = Relationship(
        back_populates="ticket",
    )
    creator: Optional["User"] = Relationship(
        back_populates="support_tickets_created",
        sa_relationship_kwargs={"foreign_keys": "[SupportTicket.created_by]"},
    )
