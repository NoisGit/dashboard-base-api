"""
Router configuration module.

This module handles the registration of all API routers with the FastAPI application.
"""

from src.routers import (
    companies_router,
    users_router,
)


def include_routers(app):
    """Include all routers in the FastAPI application."""
    app.include_router(companies_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")
