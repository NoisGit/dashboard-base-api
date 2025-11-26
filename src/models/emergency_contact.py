from __future__ import annotations

"""
Emergency contact database model for the Sentinel Enterprise API.

Represents an emergency contact associated with a specific location
(e.g. building, site). Each contact stores a name and phone number
that can be used in case of incidents.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .location import Location
    from .user import User


class EmergencyContact(SQLModel, table=True):
    __tablename__ = "emergency_contacts"

    id: Optional[int] = Field(default=None, primary_key=True)

    # DBML: location_id int
    location_id: int = Field(foreign_key="location.id")

    # DBML: name varchar(100), phone varchar(20)
    name: str = Field(max_length=100)
    phone: str = Field(max_length=20)

    # DBML: created_by int, created_at timestamp
    created_by: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    location: "Location" = Relationship(back_populates="emergency_contacts")
    creator: "User" = Relationship(
        back_populates="emergency_contacts_created",
    )
