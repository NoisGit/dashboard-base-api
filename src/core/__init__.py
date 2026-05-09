"""Core utilities and enums for the Coredeck API.

This package currently exposes:

- UserRole: global user roles enumeration for the Coredeck dashboard.
"""

from .enums import UserRole, AuditAction, TableName

__all__ = [
    "UserRole", "AuditAction", "TableName"
]
