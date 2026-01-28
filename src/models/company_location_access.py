"""User–Location Access database model for the Sentinel Enterprise API.

Represents the association between a user and a location (site/project),
including who created the link and when it was created.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .company import Company
    from .user import User
    from .location import Location


class CompanyLocationAccess(SQLModel, table=True):
    """
    Join table between companies and locations.

    A record in this table indicates that a given company has access
    to a specific location. It also keeps track of the creator user
    and the creation timestamp.

    Matches the `company_location_access` table in the ERD:

    - id
    - company_id
    - location_id
    - created_by
    - created_at
    """

    __tablename__ = "company_location_access"

    id: Optional[int] = Field(default=None, primary_key=True)

    company_id: int = Field(foreign_key="company.id", index=True)
    location_id: int = Field(foreign_key="location.id", index=True)

    created_by: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    company: "Company" = Relationship(
        back_populates="company_location_accesses",
        sa_relationship_kwargs={
            "foreign_keys": "[CompanyLocationAccess.company_id]"},
    )
    location: "Location" = Relationship(back_populates="company_locations")
    creator: "User" = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[CompanyLocationAccess.created_by]"},
    )
