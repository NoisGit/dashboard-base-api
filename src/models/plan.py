
"""
Plan database model for the Locentr API.

Represents the subscription/usage plan assigned to users, including limits
for workspaces, admins, operators and daily reads.
"""

from typing import Optional, TYPE_CHECKING, List
from sqlalchemy import BigInteger
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user import User
    from .subscription import CompanySubscription


class Plan(SQLModel, table=True):
    """
    Subscription plan entity.

    Matches the `plan` table in the ERD:

    - id
    - name
    - qty_locations
    - qty_admins
    - qty_operators
    - qty_daily_reads
    """

    __tablename__ = "plans"

    id: Optional[int] = Field(default=None, primary_key=True)

    code: str = Field(max_length=50, unique=True, index=True)

    # DBML: name varchar(100)
    name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, max_length=255)
    monthly_price_cents: int = Field(default=0, ge=0)

    # DBML: qty_locations int, qty_admins int, qty_operators int, qty_daily_reads int
    qty_locations: int
    qty_admins: int
    qty_operators: int
    qty_daily_reads: int
    qty_storage_bytes: int = Field(
        default=1024 * 1024 * 1024,
        sa_type=BigInteger,
    )
    stripe_price_id: Optional[str] = Field(default=None, max_length=100)
    is_active: bool = Field(default=True)

    # Relationships
    users: List["User"] = Relationship(back_populates="plan")
    company_subscriptions: List["CompanySubscription"] = Relationship(
        back_populates="plan",
    )
