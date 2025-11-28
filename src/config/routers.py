"""
Router configuration module.

This module handles the registration of all API routers with the FastAPI application.
"""

from fastapi import FastAPI

from src.routers import users


def include_routers(app: FastAPI) -> None:
    """Include all routers in the FastAPI application."""
    # Users router (initial version: read-only)
    app.include_router(users.router)

    # NOTE:
    # The companies router will be wired in a separate branch/PR.
    # When both PRs are merged into develop, this function should include:
    # - companies.router
    # - users.router
