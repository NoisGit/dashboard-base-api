from __future__ import annotations

"""
Custom field database model for the Sentinel Enterprise API.

Represents a dynamic field attached to a location. These fields allow
each location to store additional typed information (text, number, etc.)
and predefined values.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING, List

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .location import Location
    from .access_log_custom_field import AccessLogCustomField
    from .user import User


class CustomField(SQLModel, table=True):
    """
    Custom field entity.

    Matches the `custom_fields` table in the ERD:

    - Belongs to a Location (location_id)
    - Has a type and status
    - Stores a `values` list/definition (comma-separated, JSON, etc.)
    - Can be referenced by many AccessLogCustomField rows
    """
    __tablename__ = "custom_fields"

    id: Optional[int] = Field(default=None, primary_key=True)

    # FK to location.id
    location_id: int = Field(foreign_key="location.id")

    # DBML: name varchar(100), type varchar(20), status bool
    name: str = Field(max_length=100)
    type: str = Field(max_length=20)
    status: bool = Field(default=True)

    # ERD: values varchar(1000)
    values: str = Field(max_length=1000)

    # Audit fields (DBML: created_by int, created_at timestamp)
    created_by: int = Field(
        foreign_key="users.id",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    location: "Location" = Relationship(back_populates="custom_fields")

    # Link to access_log_custom_fields (one custom field -> many responses)
    access_log_values: List["AccessLogCustomField"] = Relationship(
        back_populates="custom_field",
    )

    # User who created this custom field
    creator: "User" = Relationship(
        back_populates="custom_fields_created",
    )
