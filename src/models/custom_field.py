from typing import Optional
from datetime import datetime

from sqlmodel import SQLModel, Field


class CustomField(SQLModel, table=True):
    __tablename__ = "custom_fields"

    id: Optional[int] = Field(default=None, primary_key=True)
    entry_id: int
    name: str
    type: str
    status: bool = True
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
