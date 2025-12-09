"""Core enums for the Sentinel Enterprise API."""

from enum import Enum


class UserRole(str, Enum):
    """Global user roles enumeration for the Enterprise dashboard."""
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    SUBADMIN = "subadmin"
    JANITOR = "janitor"
    CLIENT = "client"


__all__ = [
    "UserRole",
]
