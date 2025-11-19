from typing import Optional

from sqlmodel import SQLModel, Field


class Plan(SQLModel, table=True):
    __tablename__ = "plan"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    qty_entries: int = 0
    qty_admins: int = 0
    qty_janitors: int = 0
    qty_daily_reads: int = 0
