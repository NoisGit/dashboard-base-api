from __future__ import annotations

"""
User Entry Access database model for the Sentinel Enterprise API.

Represents the association between a user and an entry (site/company access),
including who created the link and when it was created.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user import User
    from .entries import Entries


class UserEntryAccess(SQLModel, table=True):
    """
    Join table between users and entries.

    A record in this table indicates that a given user has access
    to a specific entry. It also keeps track of the creator user
    and the creation timestamp.
    """
    __tablename__ = "user_entry_access"

    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: int = Field(foreign_key="users.id")
    entry_id: int = Field(foreign_key="entries.id")

    created_by: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: "User" = Relationship(back_populates="entry_accesses")
    entry: "Entries" = Relationship(back_populates="user_entries")
