"""
Core API endpoints module.

This module contains the basic endpoints for the Locentr API,
including health checks and protected routes.
"""
import logging
from fastapi import Depends, status
from fastapi.responses import JSONResponse
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

        payload = {
            "status": "healthy" if db_healthy else "unhealthy",
            "service": "locentr-api",
            "version": "0.0.1",
            "database": "connected" if db_healthy else "disconnected"
        }
        return JSONResponse(
            content=payload,
            status_code=(
                status.HTTP_200_OK
                if db_healthy
                else status.HTTP_503_SERVICE_UNAVAILABLE
            ),
        )
    except Exception:
        logger.exception("Health check failed")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "service": "locentr-api",
                "database": "disconnected",
            },
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


async def liveness_check():
    """Confirm that the API process is accepting requests."""
    return {
        "status": "alive",
        "service": "locentr-api",
        "version": "0.0.1",
    }


def protected_route(_=Depends(get_current_user)):
    """Endpoint that requires authentication via dependency injection."""
    return {"message": "Hola 👋"}
