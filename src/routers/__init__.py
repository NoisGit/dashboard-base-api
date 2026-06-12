"""
Router module initialization.

This module centralizes the import and export of all API routers for the
Locentr API.
"""

from .access_logs import router as access_logs_router
from .audit_log import router as audit_log_router
from .auth import router as auth_router
from .blacklists import router as blacklists_router
from .companies import router as companies_router
from .dashboard import router as dashboard_router
from .documents import router as documents_router
from .emergency_contacts import router as emergency_contacts_router
from .lifecycle import router as lifecycle_router
from .location_logbook import router as location_logbook_router
from .locations import router as locations_router
from .notifications import router as notifications_router
from .service_contacts import router as service_contacts_router
from .storage import router as storage_router
from .subscriptions import router as subscriptions_router
from .support_tickets import router as support_tickets_router
from .system import router as system_router
from .teams import router as teams_router
from .users import router as users_router
from .whitelists import router as whitelists_router

__all__ = [
    "access_logs_router",
    "audit_log_router",
    "auth_router",
    "storage_router",
    "documents_router",
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
    "subscriptions_router",
    "lifecycle_router",
    "teams_router",
    "dashboard_router",
    "location_logbook_router",
]
