"""
Access list database model for the Sentinel Enterprise API.

Represents an allowed external person for a specific location
(e.g. visitor, provider), with optional vehicle information
and an expiration date.

Matches the `access_list` table in the ERD:

- id
- location_id
- external_people_id
- name
- type_access_list_id
- reason
- vehicle_plate
- expiration_date
- file_name
- created_by
- created_at
"""

from datetime import datetime, date
from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .location import Location
    from .type_access_list import TypeAccessList
    from .external_people import ExternalPeople
    from .user import User


class AccessList(SQLModel, table=True):
    __tablename__ = "access_list"

    id: Optional[int] = Field(default=None, primary_key=True)

    # FKs
    location_id: int = Field(foreign_key="location.id")
    external_people_id: int = Field(foreign_key="external_people.id")
    type_access_list_id: int = Field(foreign_key="type_access_list.id")

    # Data
    name: str = Field(max_length=100)
    reason: Optional[str] = Field(default=None, max_length=255)
    vehicle_plate: Optional[str] = Field(default=None, max_length=20)
    expiration_date: Optional[datetime] = None
    file_name: Optional[str] = Field(default=None, max_length=255)

    # Audit
    created_by: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    location: "Location" = Relationship(back_populates="access_lists")
    external_people: "ExternalPeople" = Relationship(
        back_populates="access_lists",
    )
    type_access_list: "TypeAccessList" = Relationship(
        back_populates="access_lists",
    )
    creator: Optional["User"] = Relationship(
        back_populates="access_lists_created",
        sa_relationship_kwargs={"foreign_keys": "[AccessList.created_by]"},
    )
