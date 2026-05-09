"""Core utilities and enums for the Sentinel Enterprise API.

This package currently exposes:

- UserRole: global user roles enumeration for the Enterprise dashboard.
"""

from .enums import UserRole, AuditAction, TableName

__all__ = [
    "UserRole", "AuditAction", "TableName"
]
