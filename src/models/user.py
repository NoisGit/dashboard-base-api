from typing import Optional
from datetime import datetime

from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)

    username: str
    name: str
    password: str
    email: str

    status: bool = True

    role_id: int
    plan_id: Optional[int] = None
    company_id: Optional[int] = None

    last_session: Optional[datetime] = None
    reason_suspension: Optional[str] = None
    date_change_status: Optional[datetime] = None
    last_update: Optional[datetime] = None

    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
