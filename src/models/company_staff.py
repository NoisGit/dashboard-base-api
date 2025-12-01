"""Company staff association model for the Sentinel Enterprise API."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user import User
    from .company import Company


class CompanyStaff(SQLModel, table=True):
    """Association between a user and a company."""
    __tablename__ = "company_staff"

    id: Optional[int] = Field(default=None, primary_key=True)

    company_id: int = Field(foreign_key="company.id")
    user_id: int = Field(foreign_key="users.id")

    created_by: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    user: "User" = Relationship(
        back_populates="company_staff_memberships",
    )
    company: "Company" = Relationship(
        back_populates="staff_memberships",
    )
    creator: "User" = Relationship(
        back_populates="company_staff_created",
    )
