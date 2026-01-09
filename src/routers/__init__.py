"""
Router module initialization.

This module centralizes the import and export of all API routers for the
Sentinel Enterprise API.
"""

from .access_logs import router as access_logs_router
from .audit_log import router as audit_log_router
from .auth import router as auth_router
from .azure import router as azure_router
from .emergency_contacts import router as emergency_contacts_router
from .users import router as users_router
from .companies import router as companies_router
from .locations import router as locations_router
from .support_tickets import router as support_tickets_router
from .service_contacts import router as service_contacts_router
from .notifications import router as notifications_router
from .whitelists import router as whitelists_router
from .blacklists import router as blacklists_router
from .system import router as system_router
from .dashboard import router as dashboard_router

__all__ = [
    "access_logs_router",
    "audit_log_router",
    "auth_router",
    "azure_router",
    "emergency_contacts_router",
    "users_router",
    "companies_router",
    "locations_router",
    "support_tickets_router",
    "service_contacts_router",
    "notifications_router",
    "whitelists_router",
    "blacklists_router",
    "system_router",
    "dashboard_router",
]
