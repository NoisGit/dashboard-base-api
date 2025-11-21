from __future__ import annotations

"""
Access list database model for the Sentinel Enterprise API.

Represents an allowed external person for a specific entry
(e.g. visitor, provider), with optional vehicle information
and an expiration date.
"""

from datetime import datetime, date
from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .entries import Entries
    from .type_access_list import TypeAccessList
    from .external_people import ExternalPeople
    from .user import User


class AccessList(SQLModel, table=True):
    __tablename__ = "access_list"

    id: Optional[int] = Field(default=None, primary_key=True)

    entry_id: int = Field(foreign_key="entries.id")
    external_people_id: int = Field(foreign_key="external_people.id")
    name: str
    type_access_list_id: int = Field(foreign_key="type_access_list.id")
    reason: Optional[str] = None
    vehicle_plate: Optional[str] = None
    expiration_date: Optional[date] = None
    file_name: Optional[str] = None

    created_by: Optional[int] = Field(
        default=None,
        foreign_key="users.id",
    )
    created_at: Optional[datetime] = None

    # Relationships
    entry: "Entries" = Relationship(back_populates="access_lists")
    external_people: "ExternalPeople" = Relationship(
        back_populates="access_lists",
    )
    type_access_list: "TypeAccessList" = Relationship(
        back_populates="access_lists",
    )
    creator: Optional["User"] = Relationship(
        back_populates="access_lists_created",
    )
