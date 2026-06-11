"""
External people database model for the Locentr API.

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
    etc.) that interact with the locations.
    """

    __tablename__ = "external_people"

    id: Optional[int] = Field(default=None, primary_key=True)

    # DBML: name varchar(100), id_number varchar(50)
    name: str = Field(max_length=100)
    id_number: str = Field(max_length=50)

    # DBML: gender varchar(3) [null], file_name varchar(255) [null]
    gender: Optional[str] = Field(default=None, max_length=3)
    file_name: Optional[str] = Field(default=None, max_length=255)

    # DBML: created_by int, created_at timestamp
    created_by: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    access_lists: List["AccessList"] = Relationship(
        back_populates="external_people",
    )
    access_logs: List["AccessLog"] = Relationship(
        back_populates="external_people",
    )
    creator: Optional["User"] = Relationship(
        back_populates="external_people_created",
        sa_relationship_kwargs={"foreign_keys": "[ExternalPeople.created_by]"},
    )
