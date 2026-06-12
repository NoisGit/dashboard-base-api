"""Schemas for plans, trials, usage and billing actions."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from src.core.enums import SubscriptionStatus


class PlanResponse(BaseModel):
    """Public commercial plan representation."""

    code: str
    name: str
    description: Optional[str] = None
    monthly_price_cents: int
    qty_locations: int
    qty_admins: int
    qty_operators: int
    qty_daily_reads: int
    qty_storage_bytes: int
    checkout_available: bool


class SubscriptionUsageResponse(BaseModel):
    """Current usage measured for the root tenant."""

    locations: int
    admins: int
    operators: int
    daily_reads: int
    storage_bytes: int


class CompanySubscriptionResponse(BaseModel):
    """Subscription, trial, plan and usage visible to administrators."""

    company_id: int
    status: SubscriptionStatus
    trial_started_at: datetime
    trial_ends_at: datetime
    current_period_end: Optional[datetime] = None
    plan: PlanResponse
    usage: SubscriptionUsageResponse


class CheckoutSessionRequest(BaseModel):
    """Start or change a paid subscription through Stripe Checkout."""

    plan_code: str = Field(min_length=2, max_length=50)
    company_id: Optional[int] = Field(default=None, gt=0)


class BillingCompanyRequest(BaseModel):
    """Select a company for a billing action."""

    company_id: Optional[int] = Field(default=None, gt=0)


class BillingRedirectResponse(BaseModel):
    """Provider-hosted redirect URL."""

    url: str


class TrialCompanyRequest(BaseModel):
    """Root company details collected during self-service onboarding."""

    name: str = Field(min_length=2, max_length=100)
    activity: Optional[str] = Field(default=None, max_length=100)
    id_number: str = Field(min_length=2, max_length=50)
    type_document: str = Field(min_length=2, max_length=30)


class TrialAdminRequest(BaseModel):
    """First administrator created for a trial tenant."""

    username: str = Field(
        min_length=2,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
    )
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TrialLocationRequest(BaseModel):
    """First location created during onboarding."""

    name: str = Field(min_length=2, max_length=120)
    address: str = Field(min_length=3, max_length=255)
    country: Optional[str] = Field(default=None, max_length=80)


class StartTrialRequest(BaseModel):
    """Atomic self-service trial onboarding request."""

    company: TrialCompanyRequest
    admin: TrialAdminRequest
    location: TrialLocationRequest


class StartTrialResponse(BaseModel):
    """Authenticated result of trial onboarding."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    company_id: int
    trial_ends_at: datetime


class ReconciliationResponse(BaseModel):
    """Result returned to the scheduled billing reconciliation job."""

    expired_trials: int


__all__ = [
    "PlanResponse",
    "SubscriptionUsageResponse",
    "CompanySubscriptionResponse",
    "CheckoutSessionRequest",
    "BillingCompanyRequest",
    "BillingRedirectResponse",
    "TrialCompanyRequest",
    "TrialAdminRequest",
    "TrialLocationRequest",
    "StartTrialRequest",
    "StartTrialResponse",
    "ReconciliationResponse",
]
