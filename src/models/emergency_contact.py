from typing import Optional
from datetime import datetime

from sqlmodel import SQLModel, Field


class EmergencyContact(SQLModel, table=True):
    __tablename__ = "emergency_contacts"

    id: Optional[int] = Field(default=None, primary_key=True)
    entry_id: int
    name: str
    phone: str
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
