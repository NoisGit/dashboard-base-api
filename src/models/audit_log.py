from __future__ import annotations

"""
AuditLog database model for the Sentinel Enterprise API.

Represents an audit trail entry for user actions in the system:
- Which user performed the action
- What action was done
- Optionally on which table / record
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user import User


class AuditLog(SQLModel, table=True):
    """
    Audit log entity.

    Matches the `audit_log` table from the ERD.
    """
    __tablename__ = "audit_log"

    id: Optional[int] = Field(default=None, primary_key=True)

    # DBML: user_id int
    user_id: int = Field(foreign_key="users.id")

    # DBML: action varchar(100)
    action: str = Field(max_length=100)

    # DBML: table_name varchar(100) [null]
    table_name: Optional[str] = Field(default=None, max_length=100)

    # DBML: record_id int [null]
    record_id: Optional[int] = Field(default=None)

    # DBML: description varchar(255)
    description: str = Field(max_length=255)

    # DBML: created_at timestamp
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: "User" = Relationship(back_populates="audit_logs")
