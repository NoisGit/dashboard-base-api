"""Authentication dependencies for the FastAPI application.

This module provides authentication schemes and dependency functions
used throughout the application for securing endpoints.
"""
from fastapi.security import HTTPBearer

auth_scheme = HTTPBearer()
