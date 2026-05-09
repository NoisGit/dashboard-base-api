"""Core enums for the Coredeck API."""

from enum import Enum


class UserRole(str, Enum):
    """Global user roles enumeration for the Coredeck dashboard."""
    SUPERADMIN = "SUPERADMIN"
    ADMIN = "ADMIN"
    AGENT = "AGENT"
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


class SupportTicketStatus(str, Enum):
    """Support ticket status enumeration"""
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    CANCELED = "CANCELED"


class AccessLogImageType(str, Enum):
    """Access log image type enumeration"""
    ENTRY = "ENTRY"
    EXIT = "EXIT"


class CustomFormFieldType(str, Enum):
    """Custom form field type enumeration"""
    TEXT = "TEXT"
    NUMBER = "NUMBER"
    DROPDOWN = "DROPDOWN"
    CHECKBOX = "CHECKBOX"
    RADIO = "RADIO"


__all__ = [
    "UserRole",
    "AuditAction",
    "TableName",
    "SupportTicketStatus",
    "AccessLogImageType",
    "CustomFormFieldType",
]
