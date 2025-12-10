"""Core enums for the Sentinel Enterprise API."""

from enum import Enum


class UserRole(str, Enum):
    """Global user roles enumeration for the Enterprise dashboard."""
    SUPERADMIN = "SUPERADMIN"
    ADMIN = "ADMIN"
    SUBADMIN = "SUBADMIN"
    JANITOR = "JANITOR"
    CLIENT = "CLIENT"


__all__ = ["UserRole"]
