"""
Custom Form Field database model for the Coredeck API.

Represents a single field definition within a custom form.
Supports types: TEXT, NUMBER, DROPDOWN, CHECKBOX, RADIO.
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field, Relationship

from src.core.enums import CustomFormFieldType

if TYPE_CHECKING:
    from .custom_form import CustomForm


class CustomFormField(SQLModel, table=True):
    """
    Field definition within a custom form.

    For historical integrity, fields should be deactivated (is_active=False)
    rather than deleted.
    """
    __tablename__ = "custom_form_field"

    id: Optional[int] = Field(default=None, primary_key=True)

    form_id: int = Field(foreign_key="custom_form.id")

    # Field definition
    name: str = Field(max_length=100)
    field_type: CustomFormFieldType = Field(max_length=20)

    # Options for DROPDOWN, RADIO, CHECKBOX (stored as JSON array)
    options: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(JSONB),
    )

    is_required: bool = Field(default=False)
    display_order: int = Field(default=0)
    allow_image: bool = Field(default=False)

    # Soft delete - never hard delete for historical integrity
    is_active: bool = Field(default=True)

    # Audit
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationship
    form: "CustomForm" = Relationship(back_populates="fields")
