"""
Location logbook database models for the Sentinel Enterprise API.

This module contains SQLModel classes that represent logbook entries for a
Location, feature settings (enable/disable) and an authority access permit
used to generate a QR link for viewing logbook entries.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .location import Location
    from .user import User


class LocationLogbook(SQLModel, table=True):
    """
    Represents a logbook entry for a location.

    Matches the `location_logbook` table:

    - id
    - location_id
    - created_by
    - description
    - media_name
    - media_type
    - created_at
    """

    __tablename__ = "location_logbook"

    id: Optional[int] = Field(default=None, primary_key=True)

    location_id: int = Field(foreign_key="location.id", index=True)
    created_by: int = Field(foreign_key="users.id", index=True)

    description: str = Field(min_length=1, max_length=1000)

    media_name: Optional[str] = Field(default=None, max_length=255)
    media_type: Optional[str] = Field(default=None, max_length=20)

    created_at: datetime = Field(default_factory=datetime.now)

    location: Optional["Location"] = Relationship()
    creator: Optional["User"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[LocationLogbook.created_by]",
        },
    )


class LocationLogbookSettings(SQLModel, table=True):
    """
    Represents logbook feature settings per location.

    Admin can enable or disable the feature for a given location.
    """

    __tablename__ = "location_logbook_settings"

    id: Optional[int] = Field(default=None, primary_key=True)

    location_id: int = Field(
        foreign_key="location.id",
        index=True,
        unique=True,
    )

    is_enabled: bool = Field(default=False)

    updated_by: Optional[int] = Field(default=None, foreign_key="users.id")
    updated_at: Optional[datetime] = None

    location: Optional["Location"] = Relationship()
    updater: Optional["User"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[LocationLogbookSettings.updated_by]",
        },
    )


class PoliceAccessPermit(SQLModel, table=True):
    """
    Represents an authority access permit for a location, allowing temporary
    access via a unique token (used for QR link).
    """

    __tablename__ = "police_access_permits"

    id: Optional[int] = Field(default=None, primary_key=True)

    token: str = Field(unique=True, index=True, nullable=False)
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime = Field(nullable=False)

    location_id: int = Field(foreign_key="location.id", index=True)
    created_by: int = Field(foreign_key="users.id")

    location: Optional["Location"] = Relationship()
    creator: Optional["User"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[PoliceAccessPermit.created_by]",
        },
    )
