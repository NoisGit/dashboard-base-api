"""Core enums for the Sentinel Enterprise API."""

from enum import Enum


class UserRole(str, Enum):
    """Global user roles enumeration for the Enterprise dashboard."""
    SUPERADMIN = "SUPERADMIN"
    ADMIN = "ADMIN"
    SUBADMIN = "SUBADMIN"
    JANITOR = "JANITOR"
    CLIENT = "CLIENT"


class AuditAction(str, Enum):
    """Audit log action enumeration"""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    ACCESS_GRANTED = "ACCESS_GRANTED"
    ACCESS_DENIED = "ACCESS_DENIED"


class TableName(str, Enum):
    """Database table names enumeration"""
    USERS = "users"


__all__ = ["UserRole", "AuditAction", "TableName"]
