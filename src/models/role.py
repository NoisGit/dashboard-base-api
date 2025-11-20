from __future__ import annotations

"""
Role database model for the Sentinel Enterprise API.

Represents a user role (e.g. admin, janitor) and keeps track of when
the role record was created.
"""

from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user import User


class Role(SQLModel, table=True):
    """
    Role entity.

    Each user is associated with exactly one role, which defines
    their permissions and responsibilities in the system.
    """
    __tablename__ = "role"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(
        max_length=50,
        sa_column_kwargs={"unique": True},
    )
    created_at: Optional[datetime] = None

    # Relationships
    users: List["User"] = Relationship(back_populates="role")
