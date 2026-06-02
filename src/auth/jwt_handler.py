"""JWT token handling utilities for authentication.

This module provides functions for creating and managing JWT access and refresh tokens,
including token generation, validation, and refresh operations.
"""
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException

from src.config.config import settings
from src.core.enums import UserRole


def create_token_pair(user_id: int, role: UserRole) -> dict:
    """Generates a pair of JWT tokens (access and refresh) for a given user ID."""
    return {
        "access_token": create_access_token(user_id, role),
        "refresh_token": create_refresh_token(user_id, role),
    }


def create_access_token(user_id: int, role: UserRole) -> str:
    """Generates a JWT access token for the given user ID."""
    to_encode = {
        "user_id": user_id,
        "role": role.value,
        "exp": datetime.now(timezone.utc)
        + timedelta(minutes=settings.access_token_expire_minutes),
        "type": "access",
    }
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(user_id: int, role: UserRole) -> str:
    """Generates a JWT refresh token for a given user ID."""
    to_encode = {
        "user_id": user_id,
        "role": role.value,
        "exp": datetime.now(timezone.utc)
        + timedelta(days=settings.refresh_token_expire_days),
        "type": "refresh",
    }
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def refresh_access_token(refresh_token: str) -> str:
    """Refreshes the access token using a valid refresh token."""
    try:
        payload = jwt.decode(
            refresh_token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        user_id = payload.get("user_id")
        role = UserRole(payload.get("role"))

        return create_access_token(user_id, role)
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(status_code=401, detail="Refresh token expired") from e
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from e
