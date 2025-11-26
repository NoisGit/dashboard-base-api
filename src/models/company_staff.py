from __future__ import annotations

"""
Company staff association model for the Sentinel Enterprise API.

Represents the link between a user and a company, including who created
the relation and when it was created.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user import User
    from .company import Company


class CompanyStaff(SQLModel, table=True):
    """
    Company–staff association entity.

    Matches the `company_staff` table in the ERD:
    - One row links one user with one company
    - Tracks which user created the relation and when
    """
    __tablename__ = "company_staff"

    id: Optional[int] = Field(default=None, primary_key=True)

    company_id: int = Field(foreign_key="company.id")
    user_id: int = Field(foreign_key="users.id")

    created_by: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

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
