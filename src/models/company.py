from typing import Optional
from datetime import datetime

from sqlmodel import SQLModel, Field


class Company(SQLModel, table=True):
    __tablename__ = "company"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    giro: str
    rut: str
    logo: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
