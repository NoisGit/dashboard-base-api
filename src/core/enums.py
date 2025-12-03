"""Core enums for the Sentinel Enterprise API.

Currently contains:

- UserRole: global user roles for the Enterprise dashboard.
"""

from enum import Enum


class UserRole(str, Enum):
    """Global user roles enumeration for Enterprise."""
    ADMIN = "admin"
    JANITOR = "janitor"
    SUPERADMIN = "superadmin"
    SUBADMIN = "subadmin"
    CLIENT = "client"


__all__ = [
    "UserRole",
]
