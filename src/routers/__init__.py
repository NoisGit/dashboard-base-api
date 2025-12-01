"""
Router module initialization.

This module centralizes the import and export of all API routers for the
Sentinel Enterprise API.
"""

from .users import router as users_router

__all__ = [
    "users_router",
]
