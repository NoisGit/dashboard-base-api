from typing import Optional
from datetime import datetime

from sqlmodel import SQLModel, Field


class Entries(SQLModel, table=True):
    __tablename__ = "entries"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    address: str
    country: str
    password: Optional[str] = None
    date_last_entry: Optional[datetime] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
