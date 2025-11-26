from __future__ import annotations

"""
Access log database model for the Sentinel Enterprise API.

Represents a single access event in a location (site), linked to:
- The location where the access happened
- The external person involved
- The user who created the record
- Optional user who closed the record (exit_created_by)
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING, List

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .location import Location
    from .external_people import ExternalPeople
    from .user import User
    from .access_log_custom_field import AccessLogCustomField


class AccessLog(SQLModel, table=True):
    __tablename__ = "access_log"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign keys
    location_id: int = Field(foreign_key="location.id")
    external_people_id: int = Field(foreign_key="external_people.id")

    # Access information (DBML: [null] donde aplica)
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

    # Audit fields (DBML: created_by int, created_at timestamp)
    created_by: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    location: "Location" = Relationship(back_populates="access_logs")
    external_people: "ExternalPeople" = Relationship(
        back_populates="access_logs",
    )

    # User who created the access log
    creator: "User" = Relationship(
        back_populates="access_logs_created",
    )

    # Custom field values attached to this access log
    custom_field_values: List["AccessLogCustomField"] = Relationship(
        back_populates="access_log",
    )
