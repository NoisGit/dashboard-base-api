"""Coredeck API contract tests."""

import asyncio
import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://coredeck:coredeck@localhost:5432/coredeck_test",
)

from src.api.endpoints import root
from src.config.config import settings
from src.core.enums import UserRole
from src.main import app


def test_app_metadata_uses_coredeck_identity():
    """Validate public API metadata."""
    assert app.title == "Coredeck API"
    assert "Coredeck" in app.description


def test_root_contract_uses_coredeck_identity():
    """Validate root endpoint contract without starting the app lifespan."""
    response = asyncio.run(root())

    assert response["message"] == "Welcome to Coredeck API"
    assert response["description"] == "Portfolio-ready admin API for Coredeck"


def test_cors_origins_are_parsed_from_settings():
    """Validate local frontend CORS defaults."""
    assert "http://localhost:5173" in settings.cors_origins
    assert "http://127.0.0.1:5173" in settings.cors_origins


def test_dashboard_auth_and_storage_routes_are_registered():
    """Validate dashboard-compatible routes exist."""
    routes = {route.path for route in app.routes}

    assert "/api/v1/auth/login" in routes
    assert "/api/v1/auth/me" in routes
    assert "/api/v1/users/me" in routes
    assert "/api/v1/storage/generate_upload_url" in routes


def test_subadmin_role_is_not_available():
    """Validate removed role does not return to the public enum."""
    assert "SUBADMIN" not in {role.value for role in UserRole}
