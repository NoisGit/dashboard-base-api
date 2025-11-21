from __future__ import annotations

"""
Custom field database model for the Sentinel Enterprise API.

Represents a dynamic field attached to an entry. These fields allow
each entry to store additional typed information (text, number, etc.).
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .entries import Entries


class CustomField(SQLModel, table=True):
    __tablename__ = "custom_fields"

    id: Optional[int] = Field(default=None, primary_key=True)

    entry_id: int = Field(foreign_key="entries.id")
    name: str
    type: str
    status: bool = Field(default=True)

    created_by: Optional[int] = Field(
        default=None,
        foreign_key="users.id",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    entry: "Entries" = Relationship(back_populates="custom_fields")
