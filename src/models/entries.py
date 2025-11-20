from __future__ import annotations

"""
Entry (site) database model for the Sentinel Enterprise API.

Represents a physical or logical entry point managed by the system,
including basic metadata and relationships with users, custom fields,
emergency contacts, access lists, and access logs.
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user_entry_access import UserEntryAccess
    from .custom_field import CustomField
    from .emergency_contact import EmergencyContact
    from .access_list import AccessList
    from .access_log import AccessLog


class Entries(SQLModel, table=True):
    """
    Represents an entry (building, site, or access point) inside the system.

    Each entry can have:
    - Multiple users with access (via UserEntryAccess)
    - Custom fields to extend its metadata
    - Emergency contacts
    - Access lists (whitelists / scheduled access)
    - Access logs that record movements
    """
    __tablename__ = "entries"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    address: str
    country: str
    password: Optional[str] = None
    date_last_entry: Optional[datetime] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None

    # Relationships
    user_entries: List["UserEntryAccess"] = Relationship(back_populates="entry")
    custom_fields: List["CustomField"] = Relationship(back_populates="entry")
    emergency_contacts: List["EmergencyContact"] = Relationship(back_populates="entry")
    access_lists: List["AccessList"] = Relationship(back_populates="entry")
    access_logs: List["AccessLog"] = Relationship(back_populates="entry")
