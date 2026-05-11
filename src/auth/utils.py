"""Authentication utility functions.

This module provides utility functions for token validation, user extraction,
and authentication-related operations used throughout the application.
"""
import os
from typing import Any, Dict, Tuple

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from src.core.enums import UserRole
from .dependencies import auth_scheme

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"


def _decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        ) from e
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from e


def _ensure_access_token(payload: Dict[str, Any]) -> None:
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
) -> Dict[str, Any]:
    """Retrieve the current user by decoding the JWT token from the provided credentials."""
    payload = _decode_token(credentials.credentials)
    _ensure_access_token(payload)
    return payload


def get_user_id_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
) -> int:
    """Extract the user ID from a JWT token provided via HTTP authorization credentials."""
    payload = _decode_token(credentials.credentials)
    _ensure_access_token(payload)

    user_id = payload.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    return user_id


def get_user_id_from_refresh_token(refresh_token: str) -> int:
    """Extract the user ID from a refresh token and validate it."""
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        return user_id
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        ) from e
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        ) from e


def get_user_data_from_token(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Tuple[int, UserRole]:
    """
    Return (user_id, UserRole) from the current access token.
    """
    user_id = current_user.get("user_id")
    role_str = current_user.get("role")

    if user_id is None or role_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    try:
        role = UserRole(role_str)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid user role",
        ) from exc

    return int(user_id), role
