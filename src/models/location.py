"""
Location database model for the Sentinel Enterprise API.

Represents a physical or logical location managed by the system,
including basic metadata and relationships with users, custom fields,
emergency contacts, access lists, access logs and its owning company.
"""

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .user_location_access import UserLocationAccess
    from .company_location_access import CompanyLocationAccess
    from .custom_form import CustomForm
    from .emergency_contact import EmergencyContact
    from .service_contacts import ServiceContact
    from .access_list import AccessList
    from .access_log import AccessLog
    from .user import User
    from .company import Company


class Location(SQLModel, table=True):
    """
    Represents a location (building, site, or project) inside the system.

    Matches the `location` table in the ERD:

    - id
    - name
    - address
    - country
    - logo
    - company_id (owning company)
    - is_active
    - created_by
    - created_at
    """

    __tablename__ = "location"

    id: Optional[int] = Field(default=None, primary_key=True)

    # DBML: name varchar(100), address varchar(255)
    name: str = Field(max_length=100)
    address: str = Field(max_length=255)

    # DBML: country varchar(20) [null], logo varchar(255) [null]
    country: Optional[str] = Field(default=None, max_length=20)
    logo: Optional[str] = Field(default=None, max_length=255)

    # Owning company (can be assigned later)
    company_id: Optional[int] = Field(
        default=None,
        foreign_key="company.id",
    )

    # Soft delete flag (same pattern as User/Company)
    is_active: bool = Field(default=True)

    # DBML: created_by int, created_at timestamp
    created_by: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    company: Optional["Company"] = Relationship(
        back_populates="locations",
    )

    user_locations: List["UserLocationAccess"] = Relationship(
        back_populates="location",
    )

    company_locations: List["CompanyLocationAccess"] = Relationship(
        back_populates="location",
    )

    # Custom form for dynamic fields (optional, one per location)
    custom_form: Optional["CustomForm"] = Relationship(
        back_populates="location",
    )
    emergency_contacts: List["EmergencyContact"] = Relationship(
        back_populates="location",
    )
    service_contacts: List["ServiceContact"] = Relationship(
        back_populates="location",
    )
    access_lists: List["AccessList"] = Relationship(
        back_populates="location",
    )
    access_logs: List["AccessLog"] = Relationship(
        back_populates="location",
    )

    creator: "User" = Relationship(
        back_populates="locations_created",
        sa_relationship_kwargs={"foreign_keys": "[Location.created_by]"},
    )
