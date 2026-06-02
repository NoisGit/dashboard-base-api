"""
Core API endpoints module.

This module contains the basic endpoints for the Locentr API,
including health checks and protected routes.
"""
import logging
from fastapi import Depends
from src.auth.utils import get_current_user
from src.database import test_connection

logger = logging.getLogger(__name__)


async def root():
    """Return a welcome message, API version, and description."""
    return {
        "message": "Welcome to Locentr API",
        "version": "0.0.1",
        "description": "Portfolio-ready operations API for Locentr"
    }


async def health_check():
    """Perform a health check for the Locentr API service."""
    try:
        db_healthy = await test_connection()

        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "service": "locentr-api",
            "version": "0.0.1",
            "database": "connected" if db_healthy else "disconnected"
        }
    except Exception as e:
        logger.error("Health check failed")
        return {
            "status": "unhealthy",
            "service": "locentr-api",
            "error": str(e)
        }


def protected_route(_=Depends(get_current_user)):
    """Endpoint that requires authentication via dependency injection."""
    return {"message": "Hola 👋"}
