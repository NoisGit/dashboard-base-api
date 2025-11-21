from __future__ import annotations

"""
Emergency contact database model for the Sentinel Enterprise API.

Represents an emergency contact associated with a specific entry
(e.g. building, site). Each contact stores a name and phone number
that can be used in case of incidents.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .entries import Entries


class EmergencyContact(SQLModel, table=True):
    __tablename__ = "emergency_contacts"

    id: Optional[int] = Field(default=None, primary_key=True)

    entry_id: int = Field(foreign_key="entries.id")
    name: str
    phone: str

    created_by: Optional[int] = Field(
        default=None,
        foreign_key="users.id",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    entry: "Entries" = Relationship(back_populates="emergency_contacts")
