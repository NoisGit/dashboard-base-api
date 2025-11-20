from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class SupportTicket(SQLModel, table=True):
    __tablename__ = "support_ticket"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    comment: Optional[str] = None
    media_url: Optional[str] = None

    status: bool = Field(default=True)

    created_by: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
