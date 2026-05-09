"""
Document database model for the Coredeck API.

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
    from .company import Company


class Document(SQLModel, table=True):
    """Document ORM model for the Coredeck API."""

    __tablename__ = "documents"

    id: Optional[int] = Field(default=None, primary_key=True)

    name: str = Field(max_length=100)

    # Original file name from the upload (display/reference for users).
    # DBML: file_name varchar(255)
    file_name: str = Field(max_length=255)

    # Azure Blob object key/path (unique, no collisions).
    blob_name: str = Field(max_length=255)

    # Scope: documents belong to a company.
    company_id: int = Field(foreign_key="company.id")

    # FK to users.id (owner of the document)
    user_id: int = Field(foreign_key="users.id")

    # Optional comment/notes (DBML: text(255) [null])
    comment: Optional[str] = Field(default=None, max_length=255)

    # File metadata (useful for validations/UI/audit).
    content_type: Optional[str] = Field(default=None, max_length=100)
    size_bytes: Optional[int] = Field(default=None)

    # Audit fields (DBML: created_by int, created_at timestamp)
    created_by: int = Field(
        foreign_key="users.id",
    )
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    company: "Company" = Relationship(
        back_populates="documents",
    )

    user: "User" = Relationship(
        back_populates="documents",
        sa_relationship_kwargs={"foreign_keys": "[Document.user_id]"},
    )
    creator: Optional["User"] = Relationship(
        back_populates="documents_created",
        sa_relationship_kwargs={"foreign_keys": "[Document.created_by]"},
    )
