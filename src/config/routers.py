"""
Router configuration module.

This module handles the registration of all API routers with the FastAPI application.
"""

from src.routers import (
    audit_log_router,
    auth_router,
    emergency_contacts_router,
    companies_router,
    users_router,
    locations_router,
    support_tickets_router,
    service_contacts_router,
    whitelists_router,
)


def include_routers(app):
    """Include all routers in the FastAPI application."""
    app.include_router(audit_log_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(emergency_contacts_router, prefix="/api/v1")
    app.include_router(companies_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(locations_router, prefix="/api/v1")
    app.include_router(support_tickets_router, prefix="/api/v1")
    app.include_router(service_contacts_router, prefix="/api/v1")
    app.include_router(whitelists_router, prefix="/api/v1")
