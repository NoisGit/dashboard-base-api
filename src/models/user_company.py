from __future__ import annotations

"""
User–Company association model for the Sentinel Enterprise API.

Represents the link between a user and a company, including who created
the relation and when it was created.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user import User
    from .company import Company


class UserCompany(SQLModel, table=True):
    __tablename__ = "user_company"

    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: int = Field(foreign_key="users.id")
    company_id: int = Field(foreign_key="company.id")

    created_by: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: "User" = Relationship(back_populates="user_companies")
    company: "Company" = Relationship(back_populates="user_companies")
