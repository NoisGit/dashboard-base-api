"""Authentication utility functions.

This module provides utility functions for token validation, user extraction,
and authentication-related operations used throughout the application.
"""
import os
import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from .dependencies import auth_scheme

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    """Retrieves the current user by decoding the JWT token from the provided credentials."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(status_code=401, detail="Token expired") from e
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e


def get_user_id_from_token(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)) -> int:
    """Extracts the user ID from a JWT token provided via HTTP authorization credentials."""
    try:
        payload = jwt.decode(credentials.credentials,
                             SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        return user_id
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(status_code=401, detail="Token expired") from e
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e


def get_user_id_from_refresh_token(refresh_token: str) -> int:
    """Extracts the user ID from a refresh token and validates it."""
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])

        # Verify this is a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        return user_id
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(
            status_code=401, detail="Refresh token expired") from e
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=401, detail="Invalid refresh token") from e
