"""
Router module initialization.

This module centralizes the import and export of all API routers for the
Sentinel Enterprise API.
"""

from .audit_log import router as audit_log_router
from .auth import router as auth_router
from .emergency_contacts import router as emergency_contacts_router
from .users import router as users_router
from .companies import router as companies_router
from .locations import router as locations_router
from .support_tickets import router as support_tickets_router
from .notifications import router as notifications_router

__all__ = [
    "audit_log_router",
    "auth_router",
    "emergency_contacts_router",
    "users_router",
    "companies_router",
    "locations_router",
    "support_tickets_router",
    "notifications_router",
]
