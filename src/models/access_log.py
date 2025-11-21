from __future__ import annotations

"""
Access log database model for the Sentinel Enterprise API.

Represents a single access event in an entry (site), linked to:
- The entry where the access happened
- The external person involved
- The users who created/closed the record
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .entries import Entries
    from .external_people import ExternalPeople


class AccessLog(SQLModel, table=True):
    __tablename__ = "access_log"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign keys
    entry_id: int = Field(foreign_key="entries.id")
    external_people_id: int = Field(foreign_key="external_people.id")

    # Access information
    type_document: Optional[str] = Field(default=None, max_length=30)
    vehicle_plate: Optional[str] = Field(default=None, max_length=20)
    office: Optional[str] = Field(default=None, max_length=20)
    comment: Optional[str] = Field(default=None, max_length=100)
    photo: Optional[str] = Field(default=None, max_length=255)

    # Exit information
    exit_date: Optional[datetime] = Field(default=None)
    exit_comment: Optional[str] = Field(default=None, max_length=100)
    exit_photo: Optional[str] = Field(default=None, max_length=255)
    exit_created_by: Optional[int] = Field(
        default=None,
        foreign_key="users.id",
    )

    # Origin / metadata
    api_origin: Optional[str] = Field(default=None, max_length=255)
    type_origin: Optional[str] = Field(default=None, max_length=10)

    # Audit fields
    created_by: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    entry: "Entries" = Relationship(back_populates="access_logs")
    external_people: "ExternalPeople" = Relationship(back_populates="access_logs")
