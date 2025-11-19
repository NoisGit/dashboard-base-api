from typing import Optional
from datetime import datetime, date

from sqlmodel import SQLModel, Field


class AccessList(SQLModel, table=True):
    __tablename__ = "access_list"

    id: Optional[int] = Field(default=None, primary_key=True)

    entry_id: int
    document_id: str
    clean_document_id: Optional[str] = None
    name: str
    type_access_list_id: int
    reason: Optional[str] = None
    vehicle_plate: Optional[str] = None
    expiration_date: Optional[date] = None
    file_name: Optional[str] = None

    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
