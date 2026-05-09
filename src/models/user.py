"""User database model for the Coredeck API.

Represents a platform user (admin, agent, superadmin, etc.) and its core relationships:
- Has a role stored as varchar(10) (handled as an Enum in code)
- Belongs to a Plan
- Is linked to Companies via the company_staff join table
- Can access multiple Locations through the user_location_access join table
- Can be the creator of other records (access lists, external people, tickets, etc.).
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

from src.core.enums import UserRole

if TYPE_CHECKING:
    from .access_list import AccessList
    from .access_log import AccessLog
    from .audit_log import AuditLog
    from .company import Company
    from .company_staff import CompanyStaff
    from .custom_form import CustomForm
    from .document import Document
    from .emergency_contact import EmergencyContact
    from .service_contacts import ServiceContact
    from .external_people import ExternalPeople
    from .location import Location
    from .plan import Plan
    from .support_response import SupportResponse
    from .support_ticket import SupportTicket
    from .type_access_list import TypeAccessList
    from .user_location_access import UserLocationAccess
    from .company_location_access import CompanyLocationAccess


class User(SQLModel, table=True):
    """User ORM model for the Coredeck API."""

    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Core identity fields (match ERD: username, full_name, password_hash, email)
    username: str = Field(max_length=50, unique=True, index=True)
    full_name: str = Field(max_length=100)
    password_hash: str = Field(max_length=255)
    email: str = Field(max_length=100, unique=True, index=True)

    # DBML: status bool
    status: bool

    # Soft delete flag (business rule: DELETE -> is_active = false)
    is_active: bool = Field(default=True)

    # DBML: role varchar(10), mapped to global UserRole enum
    role: UserRole = Field(max_length=10)

    # DBML: plan_id int
    plan_id: Optional[int] = Field(default=None, foreign_key="plans.id")

    # Optional fields (DBML: [null])
    last_session: Optional[datetime] = None
    reason_suspension: Optional[str] = Field(default=None, max_length=255)
    date_change_status: Optional[datetime] = None
    last_update: Optional[datetime] = None
    refresh_token: Optional[str] = Field(default=None, max_length=255)
    fcm_token: Optional[str] = Field(default=None, max_length=255)

    # Recovery Password Fields
    reset_token: Optional[str] = Field(default=None, max_length=255)
    reset_token_expiry: Optional[datetime] = None

    # Who created this user (self-reference to users.id)
    created_by: Optional[int] = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.now)

    plan: Optional["Plan"] = Relationship(back_populates="users")

    # Access to locations via user_location_access join table
    location_accesses: List["UserLocationAccess"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={
            "foreign_keys": "[UserLocationAccess.user_id]"},
    )

    # Company–Location accesses created by this user (CompanyLocationAccess.created_by)
    company_location_accesses_created: List["CompanyLocationAccess"] = Relationship(
        back_populates="creator",
        sa_relationship_kwargs={
            "foreign_keys": "[CompanyLocationAccess.created_by]"},
    )

    # Company memberships via company_staff join table
    company_staff_memberships: List["CompanyStaff"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[CompanyStaff.user_id]"},
    )

    # Companies created by this user (Company.created_by)
    companies_created: List["Company"] = Relationship(
        back_populates="creator",
        sa_relationship_kwargs={"foreign_keys": "[Company.created_by]"},
    )

    # Documents where this user is the owner (documents.user_id)
    documents: List["Document"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[Document.user_id]"},
    )

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
        sa_relationship_kwargs={
            "foreign_keys": "[SupportResponse.created_by]",
        },
    )

    documents_created: List["Document"] = Relationship(
        back_populates="creator",
        sa_relationship_kwargs={"foreign_keys": "[Document.created_by]"},
    )

    locations_created: List["Location"] = Relationship(
        back_populates="creator",
        sa_relationship_kwargs={"foreign_keys": "[Location.created_by]"},
    )

    custom_forms_created: List["CustomForm"] = Relationship(
        back_populates="creator",
        sa_relationship_kwargs={"foreign_keys": "[CustomForm.created_by]"},
    )

    emergency_contacts_created: List["EmergencyContact"] = Relationship(
        back_populates="creator",
        sa_relationship_kwargs={
            "foreign_keys": "[EmergencyContact.created_by]",
        },
    )

    service_contacts_created: List["ServiceContact"] = Relationship(
        back_populates="creator",
        sa_relationship_kwargs={
            "foreign_keys": "[ServiceContact.created_by]",
        },
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
