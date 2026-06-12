"""Schemas for invitations, invoices and communication lifecycle."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from src.core.enums import InvitationStatus, UserRole


class InvitationCreateRequest(BaseModel):
    company_id: Optional[int] = Field(default=None, gt=0)
    location_id: Optional[int] = Field(default=None, gt=0)
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=100)
    username: str = Field(min_length=2, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    role: UserRole


class InvitationAcceptRequest(BaseModel):
    token: str = Field(min_length=20, max_length=500)
    password: str = Field(min_length=8, max_length=128)


class InvitationResponse(BaseModel):
    id: int
    company_id: int
    location_id: Optional[int]
    email: EmailStr
    full_name: str
    username: str
    role: UserRole
    status: InvitationStatus
    expires_at: datetime
    created_at: datetime


class InvitationCreatedResponse(InvitationResponse):
    invitation_url: str


class InvitationAcceptResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    company_id: int


class SeatUsageResponse(BaseModel):
    admins_used: int
    admins_limit: int
    operators_used: int
    operators_limit: int
    pending_admins: int
    pending_operators: int


class CommunicationPreferenceRequest(BaseModel):
    billing_emails: bool
    product_emails: bool
    company_id: Optional[int] = Field(default=None, gt=0)


class CommunicationPreferenceResponse(BaseModel):
    company_id: int
    billing_emails: bool
    product_emails: bool
    updated_at: datetime


class BillingInvoiceResponse(BaseModel):
    id: int
    status: str
    currency: str
    amount_due: int
    amount_paid: int
    hosted_invoice_url: Optional[str]
    invoice_pdf: Optional[str]
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    created_at: datetime


class EmailVerificationRequest(BaseModel):
    token: str = Field(min_length=20, max_length=500)


class QueueResultResponse(BaseModel):
    queued: int = 0
    sent: int = 0
    failed: int = 0


__all__ = [
    "InvitationCreateRequest",
    "InvitationAcceptRequest",
    "InvitationResponse",
    "InvitationCreatedResponse",
    "InvitationAcceptResponse",
    "SeatUsageResponse",
    "CommunicationPreferenceRequest",
    "CommunicationPreferenceResponse",
    "BillingInvoiceResponse",
    "EmailVerificationRequest",
    "QueueResultResponse",
]
