"""Security and tenant-boundary regression tests."""

import asyncio
import hashlib
import os
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.testclient import TestClient
from pydantic import ValidationError
from starlette.datastructures import Headers

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://locentr:locentr@localhost:5432/locentr_test",
)

from src.api.error import StorageServiceError
from src.config.config import settings
from src.core.enums import UserRole
from src.schemas import CompanyCreateRequest, UserCreateRequest
from src.schemas.auth_schemas import AuthRecoveryPasswordRequest
from src.security.http import SecurityMiddleware
from src.security.uploads import CSV_UPLOAD_MAX_BYTES, validate_csv_upload
from src.services.auth_service import AuthService
from src.services.company_service import CompanyService
from src.services.location_service import LocationService
from src.services.storage_service import StorageService
from src.services.user_service import UserService


def test_company_identity_fields_are_required():
    with pytest.raises(ValidationError):
        CompanyCreateRequest(name="Acme")


def test_superadmin_cannot_be_created_through_service():
    service = UserService(AsyncMock())
    payload = UserCreateRequest(
        username="root",
        full_name="Platform Root",
        email="root@locentr.com",
        password="strong-password",
        role=UserRole.SUPERADMIN,
    )

    with pytest.raises(HTTPException) as error:
        asyncio.run(service.create_user(payload))

    assert error.value.status_code == 403


def test_csv_upload_rejects_oversized_content():
    upload = UploadFile(
        filename="operators.csv",
        file=BytesIO(),
        headers=Headers({"content-type": "text/csv"}),
    )

    with pytest.raises(HTTPException) as error:
        validate_csv_upload(upload, b"x" * (CSV_UPLOAD_MAX_BYTES + 1))

    assert error.value.status_code == 413


def test_storage_rejects_mismatched_extension_and_mime():
    service = StorageService()

    with pytest.raises(StorageServiceError):
        service.generate_upload_url(
            container_name="documents",
            file_extension="exe",
            content_type="application/octet-stream",
        )


def test_storage_rejects_foreign_object_url():
    service = StorageService()

    with pytest.raises(StorageServiceError):
        service.extract_object_info_from_url(
            "https://attacker.example/documents/report.pdf"
        )


def test_password_recovery_does_not_enumerate_accounts():
    email_service = Mock()
    service = AuthService(email_service=email_service, session=AsyncMock())
    service.get_user_by_email = AsyncMock(return_value=None)

    asyncio.run(
        service.recovery_password(
            AuthRecoveryPasswordRequest(email="missing@locentr.com")
        )
    )

    email_service.send_templated_email.assert_not_called()


def test_password_recovery_stores_only_token_digest():
    email_service = Mock()
    session = Mock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    user = SimpleNamespace(
        id=4,
        email="admin@locentr.com",
        full_name="Admin Locentr",
        is_active=True,
        reset_token=None,
        reset_token_expiry=None,
    )
    service = AuthService(email_service=email_service, session=session)
    service.get_user_by_email = AsyncMock(return_value=user)

    asyncio.run(
        service.recovery_password(
            AuthRecoveryPasswordRequest(email=user.email)
        )
    )

    context = email_service.send_templated_email.call_args.kwargs["context"]
    raw_token = parse_qs(urlparse(context["reset_url"]).query)["token"][0]
    assert user.reset_token == hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    assert user.reset_token != raw_token


def test_admin_company_scope_includes_direct_subcompanies():
    session = AsyncMock()
    user_service = AsyncMock()
    user_service.get_user_by_id.return_value = SimpleNamespace(
        id=3,
        role=UserRole.ADMIN,
        is_active=True,
    )
    company_result = Mock()
    company_result.scalars.return_value.first.return_value = 10
    scope_result = Mock()
    scope_result.scalars.return_value.all.return_value = [10, 11, 12]
    session.execute.side_effect = [company_result, scope_result]

    service = CompanyService(
        session=session,
        user_service=user_service,
        storage_service=Mock(),
    )

    scope = asyncio.run(service.get_company_scope_ids(requester_id=3))

    assert scope == [10, 11, 12]


def test_security_middleware_adds_headers_and_limits_auth(monkeypatch):
    monkeypatch.setattr(settings, "auth_rate_limit_requests", 1)
    monkeypatch.setattr(settings, "auth_rate_limit_window_seconds", 60)

    app = FastAPI()
    app.add_middleware(SecurityMiddleware)

    @app.post("/api/v1/auth/login")
    async def login():
        return {"ok": True}

    with TestClient(app) as client:
        first = client.post("/api/v1/auth/login")
        second = client.post("/api/v1/auth/login")

    assert first.status_code == 200
    assert first.headers["x-content-type-options"] == "nosniff"
    assert first.headers["x-request-id"]
    assert second.status_code == 429
    assert second.headers["retry-after"]


def test_operator_requires_explicit_location_assignment():
    session = AsyncMock()
    user_service = AsyncMock()
    company_service = AsyncMock()
    storage_service = Mock()
    user_service.get_user_by_id.return_value = SimpleNamespace(
        id=7,
        role=UserRole.OPERATOR,
        is_active=True,
    )
    session.get.return_value = SimpleNamespace(id=11, is_active=True)

    scalar_result = Mock()
    scalar_result.scalars.return_value.first.return_value = None
    session.execute.return_value = scalar_result

    service = LocationService(
        session=session,
        storage_service=storage_service,
        user_service=user_service,
        company_service=company_service,
    )

    with pytest.raises(HTTPException) as error:
        asyncio.run(service.require_location_access(user_id=7, location_id=11))

    assert error.value.status_code == 403
