from __future__ import annotations

"""
External people database model for the Sentinel Enterprise API.

Represents external visitors/providers that can appear in access lists
and access logs. Each record may be linked to multiple access list
entries and multiple access log events.
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .access_list import AccessList
    from .access_log import AccessLog
    from .user import User


class ExternalPeople(SQLModel, table=True):
    """
    External people entity.

    Stores identification data for external people (visitors, providers,
    etc.) that interact with the entries.
    """
    __tablename__ = "external_people"

    id: Optional[int] = Field(default=None, primary_key=True)

    name: str
    id_number: str
    clean_id_number: Optional[str] = None
    gender: Optional[str] = None
    file_name: Optional[str] = None

    created_by: Optional[int] = Field(
        default=None,
        foreign_key="users.id",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    access_lists: List["AccessList"] = Relationship(
        back_populates="external_people",
    )
    access_logs: List["AccessLog"] = Relationship(
        back_populates="external_people",
    )
    creator: Optional["User"] = Relationship(
        back_populates="external_people_created",
    )
