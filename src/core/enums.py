"""Core enums for the Locentr API."""

from enum import Enum


class UserRole(str, Enum):
    """Global user roles enumeration for the Locentr dashboard."""

    SUPERADMIN = "SUPERADMIN"
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    CLIENT = "CLIENT"


class SubscriptionStatus(str, Enum):
    """Commercial state for a root company subscription."""

    TRIALING = "TRIALING"
    ACTIVE = "ACTIVE"
    PAST_DUE = "PAST_DUE"
    CANCELED = "CANCELED"


class InvitationStatus(str, Enum):
    """Lifecycle state for a tenant invitation."""

    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


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
    "SubscriptionStatus",
    "InvitationStatus",
    "AuditAction",
    "TableName",
    "SupportTicketStatus",
    "AccessLogImageType",
    "CustomFormFieldType",
]
