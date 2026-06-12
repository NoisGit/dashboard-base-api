"""Tenant invitations, communication preferences and billing lifecycle models."""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, UniqueConstraint
from sqlmodel import Column, Field, SQLModel

from src.core.enums import InvitationStatus, UserRole


class TenantInvitation(SQLModel, table=True):
    """Expiring, single-use invitation scoped to one tenant."""

    __tablename__ = "tenant_invitation"

    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id", index=True)
    location_id: Optional[int] = Field(default=None, foreign_key="location.id")
    invited_by: int = Field(foreign_key="users.id")
    email: str = Field(max_length=100, index=True)
    full_name: str = Field(max_length=100)
    username: str = Field(max_length=50)
    role: UserRole
    token_hash: str = Field(max_length=64, unique=True, index=True)
    status: InvitationStatus = Field(default=InvitationStatus.PENDING)
    expires_at: datetime
    accepted_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    resend_count: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class CommunicationPreference(SQLModel, table=True):
    """Company-level communication preferences."""

    __tablename__ = "communication_preference"
    __table_args__ = (
        UniqueConstraint("company_id", name="uq_communication_preference_company"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id", index=True)
    billing_emails: bool = True
    product_emails: bool = True
    updated_by: int = Field(foreign_key="users.id")
    updated_at: datetime = Field(default_factory=datetime.now)


class EmailVerificationToken(SQLModel, table=True):
    """Hashed, single-use email verification token."""

    __tablename__ = "email_verification_token"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    token_hash: str = Field(max_length=64, unique=True, index=True)
    expires_at: datetime
    consumed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)


class EmailDelivery(SQLModel, table=True):
    """Retryable transactional email outbox record."""

    __tablename__ = "email_delivery"

    id: Optional[int] = Field(default=None, primary_key=True)
    event_key: str = Field(max_length=160, unique=True, index=True)
    company_id: Optional[int] = Field(
        default=None, foreign_key="company.id", index=True
    )
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    recipient: str = Field(max_length=100)
    subject: str = Field(max_length=180)
    template_name: str = Field(max_length=100)
    context: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False),
    )
    status: str = Field(default="PENDING", max_length=20, index=True)
    attempts: int = Field(default=0, ge=0)
    last_error: Optional[str] = Field(default=None, max_length=255)
    scheduled_for: datetime = Field(default_factory=datetime.now, index=True)
    sent_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class BillingInvoice(SQLModel, table=True):
    """Sanitized invoice metadata displayed in the dashboard."""

    __tablename__ = "billing_invoice"

    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id", index=True)
    provider_invoice_id: str = Field(max_length=120, unique=True, index=True)
    status: str = Field(max_length=30)
    currency: str = Field(default="usd", max_length=10)
    amount_due: int = Field(default=0, ge=0)
    amount_paid: int = Field(default=0, ge=0)
    hosted_invoice_url: Optional[str] = Field(default=None, max_length=500)
    invoice_pdf: Optional[str] = Field(default=None, max_length=500)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
