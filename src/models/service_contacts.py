"""
Service contact database model for the Sentinel Enterprise API.

Represents a service contact associated with a specific location
(e.g. building, site). Each contact stores a name and phone number
that can be used in case of incidents.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .location import Location
    from .user import User


class ServiceContact(SQLModel, table=True):
    """Database model for service contacts."""
    __tablename__ = "service_contacts"

    id: Optional[int] = Field(default=None, primary_key=True)

    # DBML: location_id int (nullable for default country numbers)
    location_id: Optional[int] = Field(default=None, foreign_key="location.id")

    # DBML: service_name varchar(100), person_name varchar(100), email varchar(100), phone varchar(20)
    service_name: str = Field(max_length=100)
    person_name: str = Field(max_length=100)
    email: str = Field(max_length=100)
    phone: str = Field(max_length=20)

    # DBML: created_by int, created_at timestamp
    created_by: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    location: "Location" = Relationship(
        back_populates="service_contacts")
    creator: "User" = Relationship(
        back_populates="service_contacts_created",
        sa_relationship_kwargs={
            "foreign_keys": "[ServiceContact.created_by]"},
    )
