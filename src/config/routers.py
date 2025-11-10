"""
Router configuration module.

This module handles the registration of all API routers with the FastAPI application.
"""


def include_routers(_):
    """Include all routers in the FastAPI application."""

    # Example: app.include_router(users_router, prefix="/api/v1")
