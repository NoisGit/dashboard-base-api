"""
Locentr API - Main FastAPI application module.

This module initializes and configures the FastAPI application for the Locentr
platform.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.config import settings
from src.config.lifespan import lifespan
from src.config.routers import include_routers
from src.api.endpoints import root, health_check, protected_route

# Create the FastAPI application
app = FastAPI(
    title="Locentr API",
    description="Backend API for Locentr, a portfolio-ready operations platform.",
    version="0.0.5",
    lifespan=lifespan,
    swagger_ui_parameters={
        "docExpansion": "none"
    }
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers for modular API structure
include_routers(app)

# Register basic endpoints
app.get("/")(root)
app.get("/health")(health_check)
app.get("/protected")(protected_route)
