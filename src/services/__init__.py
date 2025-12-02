"""
Service module initialization.

This module centralizes the export of core service classes used for
business logic and database operations in the Sentinel Enterprise API.
"""

from .user_service import UserService

__all__ = [
    "UserService",
]
