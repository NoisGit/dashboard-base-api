"""
Access log database model for the Sentinel Enterprise API.

Represents a single access event in a location (site), linked to:
- The location where the access happened
- The external person involved
- The user who created the record
- Optional user who closed the record (exit_created_by)
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING, List, Any

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field, Relationship

from src.core.enums import AccessLogImageType

if TYPE_CHECKING:
    from .location import Location
    from .external_people import ExternalPeople
    from .user import User


class AccessLog(SQLModel, table=True):
    """Access log database model for the Sentinel Enterprise API."""
    __tablename__ = "access_log"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign keys
    location_id: int = Field(foreign_key="location.id")
    external_people_id: int = Field(foreign_key="external_people.id")

    # Access information
    type_document: Optional[str] = Field(default=None, max_length=30)
    vehicle_plate: Optional[str] = Field(default=None, max_length=20)
    office: Optional[str] = Field(default=None, max_length=20)
    comment: Optional[str] = Field(default=None, max_length=100)

    # Exit information
    exit_date: Optional[datetime] = Field(default=None)
    exit_comment: Optional[str] = Field(default=None, max_length=100)
    exit_created_by: Optional[int] = Field(
        default=None,
        foreign_key="users.id",
    )

    # Audit fields
    created_by: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.now)

    # Dynamic form responses (JSONB snapshot)
    # Structure: {
    #     "form_id": int,
    #     "responses": [{"field_id", "field_name", "field_type", "value", "options?"}]
    # }
    custom_form_responses: Optional[Any] = Field(
        default=None,
        sa_column=Column(JSONB),
    )

    # Relationships
    location: "Location" = Relationship(back_populates="access_logs")
    external_people: "ExternalPeople" = Relationship(
        back_populates="access_logs",
    )

    # User who created the access log
    creator: "User" = Relationship(
        back_populates="access_logs_created",
        sa_relationship_kwargs={"foreign_keys": "[AccessLog.created_by]"},
    )

    # Images attached to this access log (entry and exit)
    images: List["AccessLogImage"] = Relationship(back_populates="access_log")


class AccessLogImage(SQLModel, table=True):
    """Access log image database model for the Sentinel Enterprise API."""
    __tablename__ = "access_log_image"

    id: Optional[int] = Field(default=None, primary_key=True)
    access_log_id: int = Field(foreign_key="access_log.id")
    image_name: str = Field(max_length=255)
    image_type: AccessLogImageType = Field(max_length=10)
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationship
    access_log: "AccessLog" = Relationship(back_populates="images")
