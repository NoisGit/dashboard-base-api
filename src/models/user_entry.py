from typing import Optional
from datetime import datetime

from sqlmodel import SQLModel, Field


class UserEntry(SQLModel, table=True):
    __tablename__ = "user_entry"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    entry_id: int
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
