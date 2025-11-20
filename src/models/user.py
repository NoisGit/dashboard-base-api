from __future__ import annotations

"""
User database model for the Sentinel Enterprise API.

Represents a platform user (admin, janitor, etc.) and its core relationships:
- Belongs to a Role and a Plan
- Can be associated with a Company
- Can access multiple Entries through the user_entry_access join table
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .role import Role
    from .plan import Plan
    from .company import Company
    from .user_entry_access import UserEntryAccess
    from .user_company import UserCompany


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)

    username: str
    name: str
    password: str
    email: str

    status: bool = Field(default=True)

    # Foreign keys
    role_id: int = Field(foreign_key="role.id")
    plan_id: Optional[int] = Field(default=None, foreign_key="plan.id")
    company_id: Optional[int] = Field(default=None, foreign_key="company.id")

    last_session: Optional[datetime] = None
    reason_suspension: Optional[str] = None
    date_change_status: Optional[datetime] = None
    last_update: Optional[datetime] = None
    recovery_password_mode: Optional[bool] = None

    created_by: Optional[int] = None
    created_at: Optional[datetime] = None

    # Relationships
    role: Optional["Role"] = Relationship(back_populates="users")
    plan: Optional["Plan"] = Relationship(back_populates="users")
    company: Optional["Company"] = Relationship(back_populates="users")

    # Many-to-many between users and entries through user_entry_access
    entry_accesses: List["UserEntryAccess"] = Relationship(back_populates="user")

    # Link to the user_company join table
    user_companies: List["UserCompany"] = Relationship(back_populates="user")
