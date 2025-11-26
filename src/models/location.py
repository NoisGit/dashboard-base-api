from __future__ import annotations

"""
Location database model for the Sentinel Enterprise API.

Represents a physical or logical location managed by the system,
including basic metadata and relationships with users, custom fields,
emergency contacts, access lists, and access logs.
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user_location_access import UserLocationAccess
    from .custom_field import CustomField
    from .emergency_contact import EmergencyContact
    from .access_list import AccessList
    from .access_log import AccessLog
    from .user import User


class Location(SQLModel, table=True):
    """
    Represents a location (building, site, or project) inside the system.

    Matches the `location` table in the ERD:

    - id
    - name
    - address
    - country
    - logo
    - created_by
    - created_at
    """

    __tablename__ = "location"

    id: Optional[int] = Field(default=None, primary_key=True)

    # DBML: name varchar(100), address varchar(255)
    name: str = Field(max_length=100)
    address: str = Field(max_length=255)

    # DBML: country varchar(20) [null], logo varchar(255) [null]
    country: Optional[str] = Field(default=None, max_length=20)
    logo: Optional[str] = Field(default=None, max_length=255)

    # DBML: created_by int, created_at timestamp
    created_by: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    user_locations: List["UserLocationAccess"] = Relationship(
        back_populates="location",
    )
    custom_fields: List["CustomField"] = Relationship(
        back_populates="location",
    )
    emergency_contacts: List["EmergencyContact"] = Relationship(
        back_populates="location",
    )
    access_lists: List["AccessList"] = Relationship(
        back_populates="location",
    )
    access_logs: List["AccessLog"] = Relationship(
        back_populates="location",
    )

    creator: "User" = Relationship(
        back_populates="locations_created",
    )
