"""
Router module initialization.

This module centralizes the import and export of all API routers for the 
Sentinel Enterprise API.
"""

from fastapi import APIRouter

from .companies import router as companies_router

# Central API router
api_router = APIRouter()

# Register feature routers here
api_router.include_router(companies_router)

__all__ = ["api_router"]
