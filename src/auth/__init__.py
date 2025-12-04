"""Authentication package for the FastAPI application.

This package provides JWT token handling, user authentication utilities,
and authentication dependencies for securing API endpoints.
"""

from .jwt_handler import create_token_pair, refresh_access_token
from .utils import (
    get_current_user,
    get_user_id_from_token,
    get_user_id_from_refresh_token,
)
from .permissions import RoleChecker

__all__ = [
    "create_token_pair",
    "refresh_access_token",
    "get_current_user",
    "get_user_id_from_token",
    "get_user_id_from_refresh_token",
    "RoleChecker",
]
