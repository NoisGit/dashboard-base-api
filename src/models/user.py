from __future__ import annotations

"""
User database model for the Sentinel Enterprise API.

Represents a platform user (admin, janitor, superadmin, etc.) and its core relationships:
- Has a role stored as varchar(10) (handled as an Enum in code)
- Belongs to a Plan
- Is linked to Companies via the company_staff join table
- Can access multiple Locations through the user_location_access join table
- Can be the creator of other records (access lists, external people, tickets, etc.)
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .plan import Plan
    from .user_location_access import UserLocationAccess
    from .company_staff import CompanyStaff

    from .access_list import AccessList
    from .type_access_list import TypeAccessList
    from .external_people import ExternalPeople
    from .support_ticket import SupportTicket
    from .support_response import SupportResponse
    from .document import Document
    from .location import Location
    from .custom_field import CustomField
    from .emergency_contact import EmergencyContact
    from .access_log import AccessLog
    from .audit_log import AuditLog


class UserRole(str, Enum):
    """Enum for the `role` column (varchar(10)) in the users table."""
    ADMIN = "admin"
    JANITOR = "janitor"
    SUPERADMIN = "superadmin"
    SUBADMIN = "subadmin"
    CLIENT = "client"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Core identity fields (match ERD: username, full_name, password_hash, email)
    username: str = Field(max_length=50)
    full_name: str = Field(max_length=100)
    password_hash: str = Field(max_length=255)
    email: str = Field(max_length=100)

    # DBML: status bool
    status: bool

    # Soft delete flag (business rule: DELETE -> is_active = false)
    is_active: bool = Field(default=True)

    # DBML: role varchar(10)
    role: UserRole = Field(max_length=10)

    # DBML: plan_id int
    plan_id: int = Field(foreign_key="plan.id")

    # Optional fields (DBML: [null])
    last_session: Optional[datetime] = None
    reason_suspension: Optional[str] = Field(default=None, max_length=255)
    date_change_status: Optional[datetime] = None
    last_update: Optional[datetime] = None
    recovery_password_mode: Optional[bool] = None

    # Who created this user (self-reference to users.id)
    # DBML: created_by int, created_at timestamp
    created_by: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.now)

    # -----------------------------
    # Relationships (belongs-to)
    # -----------------------------
    plan: Optional["Plan"] = Relationship(back_populates="users")

    # Access to locations via user_location_access join table
    location_accesses: List["UserLocationAccess"] = Relationship(
        back_populates="user",
    )

    # Company memberships via company_staff join table
    company_staff_memberships: List["CompanyStaff"] = Relationship(
        back_populates="user",
    )

    # Documents where this user is the owner (documents.user_id)
    documents: List["Document"] = Relationship(
        back_populates="user",
    )

    # -----------------------------------
    # Audit relationships: entities
    # created by this user (created_by)
    # -----------------------------------

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

    documents_created: List["Document"] = Relationship(
        back_populates="creator",
        sa_relationship_kwargs={"foreign_keys": "[Document.created_by]"},
    )

    locations_created: List["Location"] = Relationship(
        back_populates="creator",
        sa_relationship_kwargs={"foreign_keys": "[Location.created_by]"},
    )

    custom_fields_created: List["CustomField"] = Relationship(
        back_populates="creator",
        sa_relationship_kwargs={"foreign_keys": "[CustomField.created_by]"},
    )

    emergency_contacts_created: List["EmergencyContact"] = Relationship(
        back_populates="creator",
        sa_relationship_kwargs={"foreign_keys": "[EmergencyContact.created_by]"},
    )

    access_logs_created: List["AccessLog"] = Relationship(
        back_populates="creator",
        sa_relationship_kwargs={"foreign_keys": "[AccessLog.created_by]"},
    )

    company_staff_created: List["CompanyStaff"] = Relationship(
        back_populates="creator",
        sa_relationship_kwargs={"foreign_keys": "[CompanyStaff.created_by]"},
    )

    # Audit logs where this user is referenced
    audit_logs: List["AuditLog"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[AuditLog.user_id]"},
    )
