from typing import Optional
from datetime import datetime

from sqlmodel import SQLModel, Field


class Role(SQLModel, table=True):
    __tablename__ = "role"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    created_at: Optional[datetime] = None
