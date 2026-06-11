"""Core utilities and enums for the Locentr API.

This package currently exposes:

- UserRole: global user roles enumeration for the Locentr dashboard.
"""

from .enums import UserRole, AuditAction, TableName

__all__ = [
    "UserRole", "AuditAction", "TableName"
]
