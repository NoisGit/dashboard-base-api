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
    """Database model for emergency contacts."""
    __tablename__ = "emergency_contacts"

    id: Optional[int] = Field(default=None, primary_key=True)

    # DBML: location_id int (nullable for default country numbers)
    location_id: Optional[int] = Field(default=None, foreign_key="location.id")

    # DBML: name varchar(100), phone varchar(20)
    name: str = Field(max_length=100)
    phone: str = Field(max_length=20)

    # DBML: is_default boolean (indicates if it's a default country number)
    is_default: bool = Field(default=False)

    # DBML: created_by int, created_at timestamp
    created_by: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    location: Optional["Location"] = Relationship(
        back_populates="emergency_contacts")
    creator: "User" = Relationship(
        back_populates="emergency_contacts_created",
        sa_relationship_kwargs={
            "foreign_keys": "[EmergencyContact.created_by]"},
    )
