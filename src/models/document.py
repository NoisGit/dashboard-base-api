from __future__ import annotations

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
    file_url: str = Field(max_length=255)

    # FK to users.id (owner of the document)
    user_id: int = Field(foreign_key="users.id")

    # Optional comment/notes
    comment: Optional[str] = Field(default=None, max_length=255)

    # Audit fields
    created_by: Optional[int] = Field(
        default=None,
        foreign_key="users.id",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: "User" = Relationship(back_populates="documents")
    creator: Optional["User"] = Relationship(
        back_populates="documents_created",
    )
