"""
AccessLogCustomField database model for the Sentinel Enterprise API.

Represents the value of a custom field for a given access log entry.
Each row links one `access_log` record with one `custom_fields` record
and stores the captured value.
"""

from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .access_log import AccessLog
    from .custom_field import CustomField


class AccessLogCustomField(SQLModel, table=True):
    """
    Access–custom-field response entity.

    Matches the `access_log_custom_fields` table from the ERD.
    """
    __tablename__ = "access_log_custom_fields"

    id: Optional[int] = Field(default=None, primary_key=True)

    access_log_id: int = Field(foreign_key="access_log.id")
    custom_field_id: int = Field(foreign_key="custom_fields.id")
    value: str = Field(max_length=100)

    # Relationships
    access_log: "AccessLog" = Relationship(
        back_populates="custom_field_values",
    )
    custom_field: "CustomField" = Relationship(
        back_populates="access_log_values",
    )
