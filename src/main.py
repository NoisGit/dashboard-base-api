"""
Nois Admin API - Main FastAPI application module.

This module initializes and configures the FastAPI application for the Nois
Admin platform.
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi_mcp import FastApiMCP, AuthConfig

from src.auth.utils import get_current_user
from src.config.lifespan import lifespan
from src.config.routers import include_routers
from src.api.endpoints import root, health_check, protected_route

# Create the FastAPI application
app = FastAPI(
    title="Nois Admin API",
    description="Backend API for Nois Admin, a portfolio-ready admin platform.",
    version="0.0.5",
    lifespan=lifespan,
    swagger_ui_parameters={
        "docExpansion": "none"
    }
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
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

# Create the MCP server
mcp = FastApiMCP(
    app,
    name="Nois Admin MCP",
    auth_config=AuthConfig(
        dependencies=[Depends(get_current_user)],
    )
)

mcp.mount()
