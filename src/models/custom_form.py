"""
Custom Form database model for the Locentr API.

Represents a dynamic form template attached to a location.
Each location can have at most one custom form for access log entries.
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .location import Location
    from .custom_form_field import CustomFormField
    from .user import User


class CustomForm(SQLModel, table=True):
    """
    Custom form template for a location.

    Each Location can have one CustomForm that defines
    the dynamic fields for access log entries.
    """
    __tablename__ = "custom_form"

    id: Optional[int] = Field(default=None, primary_key=True)

    # One form per location (unique constraint)
    location_id: int = Field(foreign_key="location.id", unique=True)

    is_active: bool = Field(default=True)

    # Audit fields
    created_by: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default=None)

    # Relationships
    location: "Location" = Relationship(back_populates="custom_form")
    fields: List["CustomFormField"] = Relationship(back_populates="form")

    # User who created this form
    creator: "User" = Relationship(
        back_populates="custom_forms_created",
        sa_relationship_kwargs={"foreign_keys": "[CustomForm.created_by]"},
    )
