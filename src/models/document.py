"""
Document database model for the Sentinel Enterprise API.

Represents a file uploaded/associated to a user, including:
- The target user (user_id)
- Who created the document record (created_by)
- Optional comment/annotation
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user import User


class Document(SQLModel, table=True):
    __tablename__ = "documents"

    id: Optional[int] = Field(default=None, primary_key=True)

    name: str = Field(max_length=100)
    # DBML: file_name varchar(255)
    file_name: str = Field(max_length=255)

    # FK to users.id (owner of the document)
    user_id: int = Field(foreign_key="users.id")

    # Optional comment/notes (DBML: text(255) [null])
    comment: Optional[str] = Field(default=None, max_length=255)

    # Audit fields (DBML: created_by int, created_at timestamp)
    created_by: int = Field(
        foreign_key="users.id",
    )
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    user: "User" = Relationship(
        back_populates="documents",
        sa_relationship_kwargs={"foreign_keys": "[Document.user_id]"},
    )
    creator: Optional["User"] = Relationship(
        back_populates="documents_created",
        sa_relationship_kwargs={"foreign_keys": "[Document.created_by]"},
    )
