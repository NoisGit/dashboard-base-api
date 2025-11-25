from __future__ import annotations

"""
User database model for the Sentinel Enterprise API.

Represents a platform user (admin, janitor, etc.) and its core relationships:
- Belongs to a Role and a Plan
- Can be associated with a Company
- Can access multiple Entries through the user_entry_access join table
- Can be the creator of other records (access lists, external people, etc.)
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .role import Role
    from .plan import Plan
    from .company import Company
    from .user_location_access import UserEntryAccess
    from .company_staff import UserCompany
    from .access_list import AccessList
    from .type_access_list import TypeAccessList
    from .external_people import ExternalPeople
    from .support_ticket import SupportTicket
    from .support_response import SupportResponse


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Core identity fields (match ERD: username, full_name, password_hash, email)
    username: str = Field(max_length=50)
    full_name: str = Field(max_length=100)
    password_hash: str = Field(max_length=255)
    email: str = Field(max_length=100)

    status: bool = Field(default=True)

    # Foreign keys (match ERD: role_id, plan_id, company_id)
    role_id: int = Field(foreign_key="role.id")
    plan_id: Optional[int] = Field(default=None, foreign_key="plan.id")
    company_id: Optional[int] = Field(default=None, foreign_key="company.id")

    last_session: Optional[datetime] = None
    reason_suspension: Optional[str] = Field(default=None, max_length=255)
    date_change_status: Optional[datetime] = None
    last_update: Optional[datetime] = None
    recovery_password_mode: Optional[bool] = None

    # Who created this user (self-reference to users.id)
    created_by: Optional[int] = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships (belongs-to)
    role: Optional["Role"] = Relationship(back_populates="users")
    plan: Optional["Plan"] = Relationship(back_populates="users")
    company: Optional["Company"] = Relationship(back_populates="users")

    # Many-to-many between users and entries through user_entry_access
    entry_accesses: List["UserEntryAccess"] = Relationship(back_populates="user")

    # Link to the user_company join table
    user_companies: List["UserCompany"] = Relationship(back_populates="user")

    # Audit relationships: entities created by this user
    access_lists_created: List["AccessList"] = Relationship(
        back_populates="creator",
        sa_relationship_kwargs={"foreign_keys": "[AccessList.created_by]"},
    )
    type_access_lists_created: List["TypeAccessList"] = Relationship(
        back_populates="creator",
        sa_relationship_kwargs={"foreign_keys": "[TypeAccessList.created_by]"},
    )
    external_people_created: List["ExternalPeople"] = Relationship(
        back_populates="creator",
        sa_relationship_kwargs={"foreign_keys": "[ExternalPeople.created_by]"},
    )
    support_tickets_created: List["SupportTicket"] = Relationship(
        back_populates="creator",
        sa_relationship_kwargs={"foreign_keys": "[SupportTicket.created_by]"},
    )
    support_responses_created: List["SupportResponse"] = Relationship(
        back_populates="creator",
        sa_relationship_kwargs={"foreign_keys": "[SupportResponse.created_by]"},
    )
