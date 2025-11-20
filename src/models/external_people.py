from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class ExternalPerson(SQLModel, table=True):
    __tablename__ = "external_people"

    id: Optional[int] = Field(default=None, primary_key=True)

    name: str
    id_number: str
    clean_id_number: Optional[str] = None
    gender: Optional[str] = None
    file_name: Optional[str] = None

    created_by: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
