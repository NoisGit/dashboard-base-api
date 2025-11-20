from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class SupportResponse(SQLModel, table=True):
    __tablename__ = "support_response"

    id: Optional[int] = Field(default=None, primary_key=True)

    # FK to support_ticket.id (relationships later)
    ticket_id: int

    comment: Optional[str] = None
    media_url: Optional[str] = None

    created_by: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
