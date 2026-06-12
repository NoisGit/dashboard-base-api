"""Locentr API contract tests."""

import asyncio
import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-bytes")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://locentr:locentr@localhost:5432/locentr_test",
)

from src.api.endpoints import liveness_check, root
from src.config.config import settings
from src.core.enums import UserRole
from src.main import app


def test_app_metadata_uses_locentr_identity():
    """Validate public API metadata."""
    assert app.title == "Locentr API"
    assert "Locentr" in app.description


def test_root_contract_uses_locentr_identity():
    """Validate root endpoint contract without starting the app lifespan."""
    response = asyncio.run(root())

    assert response["message"] == "Welcome to Locentr API"
    assert response["description"] == "Portfolio-ready operations API for Locentr"


def test_liveness_contract_does_not_depend_on_database():
    """Keep a process-only probe available during database incidents."""
    response = asyncio.run(liveness_check())

    assert response["status"] == "alive"


def test_cors_origins_are_parsed_from_settings():
    """Validate local frontend CORS defaults."""
    assert "http://localhost:5173" in settings.cors_origins
    assert "http://127.0.0.1:5173" in settings.cors_origins


def test_dashboard_auth_and_storage_routes_are_registered():
    """Validate dashboard-compatible routes exist."""
    routes = {route.path for route in app.routes}

    assert "/api/v1/auth/login" in routes
    assert "/api/v1/auth/me" in routes
    assert "/api/v1/auth/refresh" in routes
    assert "/api/v1/auth/refresh-access-token" not in routes
    assert "/api/v1/users/me" in routes
    assert "/api/v1/storage/generate_upload_url" in routes
    assert "/api/v1/storage/private/upload/{token}" in routes
    assert "/api/v1/storage/private/read/{token}" in routes
    assert "/api/v1/documents/upload-intent" in routes
    assert "/api/v1/subscriptions/plans" in routes
    assert "/api/v1/subscriptions/trial" in routes
    assert "/api/v1/subscriptions/me" in routes
    assert "/api/v1/subscriptions/checkout" in routes
    assert "/api/v1/subscriptions/stripe/webhook" in routes
    assert "/api/v1/subscriptions/reconcile" in routes
    assert "/api/v1/teams/invitations" in routes
    assert "/api/v1/teams/invitations/accept" in routes
    assert "/api/v1/teams/seats" in routes
    assert "/api/v1/lifecycle/preferences" in routes
    assert "/api/v1/lifecycle/invoices" in routes
    assert "/api/v1/lifecycle/verify-email" in routes
    assert "/api/v1/lifecycle/queue/process" in routes
    assert "/api/v1/notifications/me/unread" in routes
    assert "/api/v1/notifications/send-all-users" in routes
    assert "/live" in routes
    assert "/ready" in routes


def test_notification_routes_use_expected_http_methods():
    """Keep notification routes aligned with the dashboard service."""
    routes = {
        route.path: set(route.methods or [])
        for route in app.routes
        if hasattr(route, "methods")
    }

    assert routes["/api/v1/notifications/send-all-users"] == {"POST"}
    assert routes["/api/v1/notifications/me/unread"] == {"GET"}
    assert routes["/api/v1/notifications/me/mark-read/{notification_id}"] == {"PUT"}


def test_subadmin_role_is_not_available():
    """Validate removed role does not return to the public enum."""
    assert "SUBADMIN" not in {role.value for role in UserRole}
