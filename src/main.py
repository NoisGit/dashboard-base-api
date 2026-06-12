"""
Locentr API - Main FastAPI application module.

This module initializes and configures the FastAPI application for the Locentr
platform.
"""

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from src.api.endpoints import health_check, liveness_check, protected_route, root
from src.api.error_contract import (
    OPENAPI_ERROR_EXAMPLE,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from src.config.config import settings
from src.config.lifespan import lifespan
from src.config.routers import include_routers
from src.security.http import SecurityMiddleware

# Create the FastAPI application
app = FastAPI(
    title="Locentr API",
    description="Backend API for Locentr, a portfolio-ready operations platform.",
    version="0.0.5",
    lifespan=lifespan,
    swagger_ui_parameters={"docExpansion": "none"},
    responses={
        400: {
            "description": "Versioned Locentr API error",
            "content": {"application/json": {"example": OPENAPI_ERROR_EXAMPLE}},
        }
    },
)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.add_middleware(SecurityMiddleware)

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
app.get("/live")(liveness_check)
app.get("/ready")(health_check)
app.get("/protected")(protected_route)
