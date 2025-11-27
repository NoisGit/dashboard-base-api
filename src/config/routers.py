"""
Router configuration module.

This module handles the registration of all API routers with the FastAPI application.
"""

from fastapi import FastAPI

from src.routers import companies


def include_routers(app: FastAPI) -> None:
    """Include all routers in the FastAPI application."""
    # Companies CRUD router
    app.include_router(companies.router)

    # Example: app.include_router(users_router, prefix="/api/v1")