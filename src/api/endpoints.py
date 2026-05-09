"""
Core API endpoints module.

This module contains the basic endpoints for the Coredeck API,
including health checks and protected routes.
"""
import logging
from fastapi import Depends
from src.auth.utils import get_current_user
from src.database import test_connection

logger = logging.getLogger(__name__)


async def root():
    """Asynchronous endpoint that returns a welcome message, API version, and description."""
    return {
        "message": "Welcome to Coredeck API",
        "version": "0.0.1",
        "description": "Portfolio-ready admin API for Coredeck"
    }


async def health_check():
    """Performs a health check for the Coredeck API service."""
    try:
        db_healthy = await test_connection()

        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "service": "coredeck-api",
            "version": "0.0.1",
            "database": "connected" if db_healthy else "disconnected"
        }
    except Exception as e:
        logger.error("Health check failed")
        return {
            "status": "unhealthy",
            "service": "coredeck-api",
            "error": str(e)
        }


def protected_route(_=Depends(get_current_user)):
    """Endpoint that requires authentication via dependency injection."""
    return {"message": "Hola 👋"}
