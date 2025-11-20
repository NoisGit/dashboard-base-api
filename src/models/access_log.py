from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class AccessLog(SQLModel, table=True):
    __tablename__ = "access_log"

    id: Optional[int] = Field(default=None, primary_key=True)

    entry_id: Optional[int] = None
    external_people_id: Optional[int] = None

    type_document: Optional[str] = None
    vehicle_plate: Optional[str] = None
    office: Optional[str] = None
    comment: Optional[str] = None
    photo: Optional[str] = None

    exit_date: Optional[datetime] = None
    exit_comment: Optional[str] = None
    exit_photo: Optional[str] = None
    exit_created_by: Optional[int] = None

    api_origin: Optional[str] = None
    type_origin: Optional[str] = None

    created_by: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
