"""Company subscription and billing webhook models."""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from src.core.enums import SubscriptionStatus

if TYPE_CHECKING:
    from .company import Company
    from .plan import Plan


class CompanySubscription(SQLModel, table=True):
    """One commercial subscription owned by one root company."""

    __tablename__ = "company_subscription"
    __table_args__ = (
        UniqueConstraint("company_id", name="uq_company_subscription_company"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id", index=True)
    plan_id: int = Field(foreign_key="plans.id", index=True)
    status: SubscriptionStatus = Field(default=SubscriptionStatus.TRIALING)
    trial_started_at: datetime
    trial_ends_at: datetime
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    provider: str = Field(default="stripe", max_length=30)
    provider_customer_id: Optional[str] = Field(
        default=None,
        max_length=100,
        index=True,
    )
    provider_subscription_id: Optional[str] = Field(
        default=None,
        max_length=100,
        unique=True,
    )
    canceled_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    company: "Company" = Relationship(back_populates="subscription")
    plan: "Plan" = Relationship(back_populates="company_subscriptions")


class BillingEvent(SQLModel, table=True):
    """Processed provider event used to make webhooks idempotent."""

    __tablename__ = "billing_event"

    id: Optional[int] = Field(default=None, primary_key=True)
    provider: str = Field(default="stripe", max_length=30)
    provider_event_id: str = Field(max_length=120, unique=True, index=True)
    event_type: str = Field(max_length=120)
    processed_at: datetime = Field(default_factory=datetime.now)
