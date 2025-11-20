from __future__ import annotations

"""
Company database model for the Sentinel Enterprise API.

Represents a client company that uses the platform. A company:
- Can have multiple users associated with it
- Is linked to users through both a direct FK (users.company_id)
  and the user_company join table
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user import User
    from .user_company import UserCompany


class Company(SQLModel, table=True):
    """
    Core company entity.

    Matches the `company` table in the ERD:
    - Basic identification (name, giro, rut)
    - Optional logo
    - Audit fields for who created the record and when
    """
    __tablename__ = "company"

    id: Optional[int] = Field(default=None, primary_key=True)

    name: str
    giro: str
    rut: str
    logo: Optional[str] = None

    created_by: Optional[int] = None
    created_at: Optional[datetime] = None

    # Relationships
    # One company can be referenced directly by many users (users.company_id)
    users: List["User"] = Relationship(back_populates="company")

    # One company can also be linked to many users via the user_company join table
    user_companies: List["UserCompany"] = Relationship(back_populates="company")
