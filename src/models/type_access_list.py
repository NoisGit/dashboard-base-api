from __future__ import annotations

"""
TypeAccessList database model for the Sentinel Enterprise API.

Represents the type/category of an access list entry (e.g. visitor,
provider, delivery, etc.). Each AccessList row is associated with exactly
one TypeAccessList.
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .access_list import AccessList
    from .user import User


class TypeAccessList(SQLModel, table=True):
    """
    TypeAccessList entity.

    Represents a category for access list entries (visitor, provider,
    delivery, etc.) and tracks which user created the record.
    """

    __tablename__ = "type_access_list"

    id: Optional[int] = Field(default=None, primary_key=True)

    # DBML: name varchar(100)
    name: str = Field(max_length=100)

    # DBML: created_by int, created_at timestamp
    created_by: int = Field(
        foreign_key="users.id",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    access_lists: List["AccessList"] = Relationship(
        back_populates="type_access_list",
    )
    creator: Optional["User"] = Relationship(
        back_populates="type_access_lists_created",
    )
