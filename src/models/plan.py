from __future__ import annotations

"""
Plan database model for the Sentinel Enterprise API.

Represents the subscription/usage plan assigned to users, including limits
for entries, admins, janitors and daily reads.
"""

from typing import Optional, List, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user import User


class Plan(SQLModel, table=True):
    """
    Subscription plan entity.

    Each plan defines the allowed quantities of entries, admins, janitors
    and daily reads for the company.
    """
    __tablename__ = "plan"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)

    qty_entries: int = 0
    qty_admins: int = 0
    qty_janitors: int = 0
    qty_daily_reads: int = 0

    # Relationships
    users: List["User"] = Relationship(back_populates="plan")
