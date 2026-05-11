"""Auth token contract tests."""

import os

os.environ.setdefault("SECRET_KEY", "test-secret-key")

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from src.auth import create_token_pair
from src.auth.utils import get_current_user, get_user_id_from_refresh_token
from src.core.enums import UserRole


def _credentials(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )


def test_access_token_is_valid_for_protected_routes():
    """Validate access tokens work on protected routes."""
    token_pair = create_token_pair(user_id=1, role=UserRole.SUPERADMIN)

    payload = get_current_user(_credentials(token_pair["access_token"]))

    assert payload["user_id"] == 1
    assert payload["role"] == UserRole.SUPERADMIN.value
    assert payload["type"] == "access"


def test_refresh_token_is_not_valid_for_protected_routes():
    """Validate refresh tokens cannot be used as access tokens."""
    token_pair = create_token_pair(user_id=1, role=UserRole.SUPERADMIN)

    with pytest.raises(HTTPException) as exc:
        get_current_user(_credentials(token_pair["refresh_token"]))

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid token type"


def test_refresh_token_extracts_user_id():
    """Validate refresh tokens still work for refresh flow."""
    token_pair = create_token_pair(user_id=1, role=UserRole.SUPERADMIN)

    user_id = get_user_id_from_refresh_token(token_pair["refresh_token"])

    assert user_id == 1
