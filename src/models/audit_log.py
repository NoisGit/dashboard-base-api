"""
AuditLog database model for the Locentr API.

Represents an audit trail entry for user actions in the system:
- Which user performed the action
- What action was done
- Optionally on which table / record
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Enum as SaEnum, Index
from sqlmodel import SQLModel, Field, Relationship, Column

from src.core import AuditAction, TableName

if TYPE_CHECKING:
    from .user import User


class AuditLog(SQLModel, table=True):
    """
    Audit log entity.

    Matches the `audit_log` table from the ERD.
    """
    __tablename__ = "audit_log"
    __table_args__ = (
        Index("ix_audit_log_created_at", "created_at"),
        Index("ix_audit_log_user_created_at", "user_id", "created_at"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    # DBML: user_id int
    user_id: int = Field(foreign_key="users.id")

    # DBML: action varchar(100)
    action: AuditAction = Field(
        sa_column=Column(SaEnum(AuditAction), nullable=False)
    )

    # DBML: table_name varchar(100) [null]
    table_name: Optional[TableName] = Field(
        default=None,
        sa_column=Column(SaEnum(TableName), nullable=True)
    )

    # DBML: record_id int [null]
    record_id: Optional[int] = Field(default=None)

    # DBML: description varchar(255)
    description: str = Field(max_length=255)

    # DBML: created_at timestamp
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    user: "User" = Relationship(back_populates="audit_logs")
