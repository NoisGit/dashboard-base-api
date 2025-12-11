"""JWT token handling utilities for authentication.

This module provides functions for creating and managing JWT access and refresh tokens,
including token generation, validation, and refresh operations.
"""
import os
from datetime import datetime, timedelta, timezone
import jwt
from dotenv import load_dotenv
from fastapi import HTTPException
from src.core.enums import UserRole


load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAY = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_DAY") or 1)
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS") or 30)


def create_token_pair(user_id: int, role: UserRole) -> dict:
    """Generates a pair of JWT tokens (access and refresh) for a given user ID."""
    return {
        "access_token": create_access_token(user_id, role),
        "refresh_token": create_refresh_token(user_id, role)
    }


def create_access_token(user_id: int, role: UserRole) -> str:
    """Generates a JWT access token for the given user ID."""
    to_encode = {
        "user_id": user_id,
        "role": role.value,
        "exp": datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAY),
        "type": "access"
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int, role: UserRole) -> str:
    """Generates a JWT refresh token for a given user ID."""
    to_encode = {
        "user_id": user_id,
        "role": role.value,
        "exp": datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "type": "refresh"
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def refresh_access_token(refresh_token: str) -> str:
    """Refreshes the access token using a valid refresh token."""
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY,
                             algorithms=[ALGORITHM])

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        user_id = payload.get("user_id")
        role = UserRole(payload.get("role"))

        return create_access_token(user_id, role)
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(
            status_code=401, detail="Refresh token expired") from e
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=401, detail="Invalid refresh token") from e
