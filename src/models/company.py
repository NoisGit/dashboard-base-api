"""Company database model for the Sentinel Enterprise API.

Represents a client company that uses the platform.

Matches the `company` table in the ERD:
- Basic identification (name)
- Optional activity and id_number
- Optional logo and document type
- Soft delete flag (is_active)
- Audit fields for who created the record and when
"""

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .company_staff import CompanyStaff
    from .user import User
    from .location import Location


class Company(SQLModel, table=True):
    """Core company entity aligned with the new ERD."""

    __tablename__ = "company"

    id: Optional[int] = Field(default=None, primary_key=True)

    name: str = Field(max_length=100)
    activity: Optional[str] = Field(default=None, max_length=100)
    id_number: Optional[str] = Field(default=None, max_length=50)
    logo: Optional[str] = Field(default=None, max_length=255)
    type_document: Optional[str] = Field(default=None, max_length=30)

    # Soft delete flag: use is_active = False instead of physical delete
    is_active: bool = Field(default=True)

    # Audit fields
    created_by: int = Field(
        foreign_key="users.id",
    )
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    # Company is linked to users through the company_staff join table
    staff_memberships: List["CompanyStaff"] = Relationship(
        back_populates="company",
    )

    # Locations owned by this company
    locations: List["Location"] = Relationship(
        back_populates="company",
    )

    # User who created this company
    creator: "User" = Relationship(
        back_populates="companies_created",
        sa_relationship_kwargs={"foreign_keys": "[Company.created_by]"},
    )
