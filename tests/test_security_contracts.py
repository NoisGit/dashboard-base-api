"""Security and tenant-boundary regression tests."""

import asyncio
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timedelta
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.testclient import TestClient
from pydantic import ValidationError
from starlette.datastructures import Headers

os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-bytes")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://locentr:locentr@localhost:5432/locentr_test",
)

from src.api.error import StorageServiceError
from src.auth.jwt_handler import create_refresh_token
from src.config.config import Settings, settings
from src.core.enums import SubscriptionStatus, UserRole
from src.schemas import AccessLogExitRequest, CompanyCreateRequest, UserCreateRequest
from src.schemas.auth_schemas import AuthRecoveryPasswordRequest
from src.security.http import SecurityMiddleware
from src.security.uploads import CSV_UPLOAD_MAX_BYTES, validate_csv_upload
from src.services.access_log_service import AccessLogService
from src.services.auth_service import AuthService
from src.services.company_service import CompanyService
from src.services.dashboard_service import DashboardService
from src.services.document_service import DocumentService
from src.services.location_service import LocationService
from src.services.location_logbook_service import LocationLogbookService
from src.services.notification_service import NotificationService
from src.services.storage_service import StorageService
from src.services.support_ticket_service import SupportTicketService
from src.services.subscription_service import SubscriptionService
from src.services.user_service import UserService


def test_company_identity_fields_are_required():
    with pytest.raises(ValidationError):
        CompanyCreateRequest(name="Acme")


@pytest.mark.parametrize(
    ("secret_key", "cors_origins"),
    [
        ("short-production-secret", "https://app.locentr.example"),
        ("x" * 32, "*"),
    ],
)
def test_production_rejects_unsafe_auth_or_cors_settings(
    secret_key,
    cors_origins,
):
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            ENV="production",
            SECRET_KEY=secret_key,
            DATABASE_URL=(
                "postgresql+asyncpg://locentr:locentr@localhost/locentr"
            ),
            BACKEND_CORS_ORIGINS=cors_origins,
        )


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


def test_private_document_upload_and_read_are_company_bound(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(settings, "private_storage_root", str(tmp_path))
    service = StorageService()
    content = b"%PDF-1.7 private document"
    intent = service.generate_document_upload_intent(
        company_id=10,
        file_name="report.pdf",
        content_type="application/pdf",
        size_bytes=len(content),
    )
    upload_token = intent["upload_url"].rsplit("/", 1)[-1]

    object_name = service.store_private_upload(
        upload_token,
        content,
        "application/pdf",
    )
    service.ensure_private_document_exists(object_name, company_id=10)

    with pytest.raises(StorageServiceError):
        service.ensure_private_document_exists(object_name, company_id=11)

    read_url = service.generate_private_read_url(
        object_name=object_name,
        company_id=10,
        file_name="report.pdf",
        content_type="application/pdf",
    )
    read_token = read_url.rsplit("/", 1)[-1]
    path, file_name, content_type = service.resolve_private_read(read_token)

    assert path.read_bytes() == content
    assert file_name == "report.pdf"
    assert content_type == "application/pdf"


def test_private_document_upload_rejects_tampered_size(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(settings, "private_storage_root", str(tmp_path))
    service = StorageService()
    intent = service.generate_document_upload_intent(
        company_id=10,
        file_name="report.pdf",
        content_type="application/pdf",
        size_bytes=20,
    )
    token = intent["upload_url"].rsplit("/", 1)[-1]

    with pytest.raises(StorageServiceError):
        service.store_private_upload(token, b"too short", "application/pdf")


def test_subscription_rejects_provisioning_when_plan_limit_is_reached():
    service = SubscriptionService(AsyncMock())
    service._subscription = AsyncMock(
        return_value=SimpleNamespace(
            company_id=10,
            status=SubscriptionStatus.TRIALING,
            plan=SimpleNamespace(
                qty_locations=2,
                qty_admins=2,
                qty_operators=10,
                qty_daily_reads=500,
                qty_storage_bytes=1024,
            ),
        )
    )
    service.usage = AsyncMock(
        return_value=SimpleNamespace(
            locations=2,
            admins=1,
            operators=3,
            daily_reads=20,
            storage_bytes=100,
        )
    )

    with pytest.raises(HTTPException) as error:
        asyncio.run(service.enforce_limit(10, "locations"))

    assert error.value.status_code == 409


def test_subscription_rejects_provisioning_after_trial_ends():
    service = SubscriptionService(AsyncMock())
    service._subscription = AsyncMock(
        return_value=SimpleNamespace(
            company_id=10,
            status=SubscriptionStatus.CANCELED,
            plan=SimpleNamespace(),
        )
    )

    with pytest.raises(HTTPException) as error:
        asyncio.run(service.enforce_limit(10, "storage_bytes", 100))

    assert error.value.status_code == 402


def test_stripe_status_mapping_revokes_terminal_subscriptions():
    service = SubscriptionService(AsyncMock())

    assert service._map_stripe_status("active") == SubscriptionStatus.ACTIVE
    assert (
        service._map_stripe_status("past_due")
        == SubscriptionStatus.PAST_DUE
    )
    assert (
        service._map_stripe_status("canceled")
        == SubscriptionStatus.CANCELED
    )


def test_stripe_webhook_retries_are_idempotent(monkeypatch):
    secret = "whsec_test_locentr"
    monkeypatch.setattr(settings, "STRIPE_WEBHOOK_SECRET", secret)
    session = Mock()
    session.add = Mock()
    session.commit = AsyncMock()
    missing = Mock()
    missing.scalars.return_value.first.return_value = None
    existing = Mock()
    existing.scalars.return_value.first.return_value = SimpleNamespace(id=1)
    session.execute = AsyncMock(side_effect=[missing, existing])
    service = SubscriptionService(session)
    service._apply_stripe_event = AsyncMock()

    payload = json.dumps(
        {
            "id": "evt_locentr_retry",
            "object": "event",
            "type": "customer.subscription.updated",
            "data": {"object": {"metadata": {}}},
        },
        separators=(",", ":"),
    ).encode("utf-8")
    timestamp = int(time.time())
    signature = hmac.new(
        secret.encode("utf-8"),
        f"{timestamp}.{payload.decode('utf-8')}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    header = f"t={timestamp},v1={signature}"

    asyncio.run(service.process_stripe_webhook(payload, header))
    asyncio.run(service.process_stripe_webhook(payload, header))

    service._apply_stripe_event.assert_awaited_once()
    session.add.assert_called_once()
    session.commit.assert_awaited_once()


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


def test_refresh_tokens_are_unique_hashed_and_rotated():
    session = Mock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    user = SimpleNamespace(
        id=4,
        role=UserRole.ADMIN,
        is_active=True,
        refresh_token=None,
    )
    service = AuthService(email_service=Mock(), session=session)
    service.get_user_by_id = AsyncMock(return_value=user)

    first_token = create_refresh_token(user.id, user.role)
    second_token = create_refresh_token(user.id, user.role)

    assert first_token != second_token

    asyncio.run(service.update_refresh_token(user.id, first_token))

    assert user.refresh_token == hashlib.sha256(
        first_token.encode("utf-8")
    ).hexdigest()
    assert asyncio.run(service._get_user_from_refresh_token(first_token)) is user

    asyncio.run(service.update_refresh_token(user.id, second_token))

    with pytest.raises(HTTPException) as error:
        asyncio.run(service._get_user_from_refresh_token(first_token))

    assert error.value.status_code == 401


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


def test_admin_cannot_access_foreign_company():
    session = AsyncMock()
    user_service = AsyncMock()
    user_service.get_user_by_id.return_value = SimpleNamespace(
        id=3,
        role=UserRole.ADMIN,
        is_active=True,
    )
    session.get.return_value = SimpleNamespace(id=99, is_active=True)
    service = CompanyService(
        session=session,
        user_service=user_service,
        storage_service=Mock(),
    )
    service.get_company_scope_ids = AsyncMock(return_value=[10, 11])

    with pytest.raises(HTTPException) as error:
        asyncio.run(
            service.require_company_access(
                requester_id=3,
                company_id=99,
            )
        )

    assert error.value.status_code == 403


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


def test_security_middleware_rejects_excess_inflight_requests(monkeypatch):
    monkeypatch.setattr(settings, "max_concurrent_requests", 1)
    middleware = SecurityMiddleware(FastAPI())

    assert asyncio.run(middleware._try_acquire_capacity()) is True
    assert asyncio.run(middleware._try_acquire_capacity()) is False

    asyncio.run(middleware._release_capacity())
    assert asyncio.run(middleware._try_acquire_capacity()) is True


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


def test_operator_cannot_register_exit_for_unassigned_location():
    session = AsyncMock()
    access_log = SimpleNamespace(
        id=31,
        location_id=22,
        exit_date=None,
    )
    result = Mock()
    result.scalar_one_or_none.return_value = access_log
    session.execute.return_value = result

    location_service = AsyncMock()
    location_service.check_user_permission_on_location.side_effect = HTTPException(
        status_code=403,
        detail="Not allowed for this location.",
    )
    service = AccessLogService(
        session=session,
        storage_service=Mock(),
        user_service=AsyncMock(),
        location_service=location_service,
    )

    with pytest.raises(HTTPException) as error:
        asyncio.run(
            service.register_exit(
                access_log_id=access_log.id,
                payload=AccessLogExitRequest(),
                exit_created_by=7,
            )
        )

    assert error.value.status_code == 403
    session.commit.assert_not_awaited()


def test_admin_cannot_download_foreign_company_document():
    session = AsyncMock()
    document = SimpleNamespace(id=41, company_id=99)
    foreign_company = SimpleNamespace(
        id=99,
        parent_company_id=None,
        is_active=True,
    )
    session.get.side_effect = [document, foreign_company]
    company_result = Mock()
    company_result.first.return_value = (10,)
    session.execute.return_value = company_result

    user_service = AsyncMock()
    user_service.get_user_by_id.return_value = SimpleNamespace(
        id=3,
        role=UserRole.ADMIN,
        is_active=True,
    )
    service = DocumentService(
        session=session,
        user_service=user_service,
        storage_service=Mock(),
    )

    with pytest.raises(HTTPException) as error:
        asyncio.run(
            service.get_document_download_url(
                user_id=3,
                document_id=document.id,
            )
        )

    assert error.value.status_code == 403


def test_user_cannot_read_another_users_support_ticket():
    session = AsyncMock()
    ticket = SimpleNamespace(id=51, created_by=9)
    ticket_result = Mock()
    ticket_result.scalars.return_value.first.return_value = ticket
    session.execute.return_value = ticket_result

    user_service = AsyncMock()
    user_service.get_user_by_id.return_value = SimpleNamespace(
        id=7,
        role=UserRole.ADMIN,
        is_active=True,
    )
    service = SupportTicketService(
        session=session,
        user_service=user_service,
        storage_service=Mock(),
    )

    with pytest.raises(HTTPException) as error:
        asyncio.run(
            service.get_support_ticket_detail(
                ticket_id=ticket.id,
                user_id=7,
            )
        )

    assert error.value.status_code == 403


def test_user_cannot_mark_another_users_notification_as_read():
    session = AsyncMock()
    notification = SimpleNamespace(id=61, user_id=9, read_at=None)
    service = NotificationService(
        session=session,
        user_service=AsyncMock(),
    )
    service.get_notification_by_id = AsyncMock(return_value=notification)

    with pytest.raises(HTTPException) as error:
        asyncio.run(
            service.mark_notification_as_read(
                user_id=7,
                notification_id=notification.id,
            )
        )

    assert error.value.status_code == 404
    session.commit.assert_not_awaited()


def test_dashboard_rejects_foreign_location_before_querying_stats():
    session = AsyncMock()
    location_service = AsyncMock()
    location_service.check_user_permission_on_location.side_effect = HTTPException(
        status_code=403,
        detail="Not allowed for this location.",
    )
    service = DashboardService(
        session=session,
        user_service=AsyncMock(),
        location_service=location_service,
    )

    with pytest.raises(HTTPException) as error:
        asyncio.run(
            service.get_dashboard_stats(
                user_id=7,
                location_id=22,
            )
        )

    assert error.value.status_code == 403
    session.execute.assert_not_awaited()


def test_dashboard_returns_zero_access_list_kpis_on_clean_database():
    session = AsyncMock()
    service = DashboardService(
        session=session,
        user_service=AsyncMock(),
        location_service=AsyncMock(),
    )
    service.get_type_list = AsyncMock(return_value=None)

    whitelist = asyncio.run(service.get_kpis_whitelist(location_id=22))
    blacklist = asyncio.run(service.get_kpis_blacklist(location_id=22))

    assert whitelist.total == 0
    assert whitelist.today == 0
    assert blacklist.total == 0
    session.execute.assert_not_awaited()


def test_police_access_token_is_consumed_once_with_row_lock():
    session = AsyncMock()
    permit = SimpleNamespace(
        location_id=11,
        location=SimpleNamespace(name="Central"),
        expires_at=datetime.now() + timedelta(minutes=5),
    )
    permit_result = Mock()
    permit_result.scalar_one_or_none.return_value = permit
    entries_result = Mock()
    entries_result.scalars.return_value.all.return_value = []
    missing_result = Mock()
    missing_result.scalar_one_or_none.return_value = None
    session.execute.side_effect = [
        permit_result,
        entries_result,
        missing_result,
    ]

    service = LocationLogbookService(
        session=session,
        storage_service=Mock(),
        location_service=AsyncMock(),
    )

    response = asyncio.run(service.view_logs_police("one-time-token"))

    assert response.location_name == "Central"
    assert session.execute.call_args_list[0].args[0]._for_update_arg is not None
    session.delete.assert_awaited_once_with(permit)
    session.commit.assert_awaited_once()

    with pytest.raises(HTTPException) as error:
        asyncio.run(service.view_logs_police("one-time-token"))

    assert error.value.status_code == 404


def test_new_police_link_invalidates_previous_links_for_location():
    session = Mock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    service = LocationLogbookService(
        session=session,
        storage_service=Mock(),
        location_service=AsyncMock(),
    )
    service._assert_logbook_enabled = AsyncMock()

    response = asyncio.run(
        service.create_police_access_path(
            user_id=7,
            location_id=11,
        )
    )

    raw_token = response.relative_path.rsplit("/", 1)[-1]
    permit = session.add.call_args.args[0]
    delete_statement = session.execute.call_args.args[0]

    assert permit.location_id == 11
    assert permit.token == hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    assert permit.token != raw_token
    assert delete_statement.compile().params["location_id_1"] == 11


def test_police_link_cannot_be_created_for_foreign_location():
    session = Mock()
    location_service = AsyncMock()
    location_service.check_user_permission_on_location.side_effect = HTTPException(
        status_code=403,
        detail="Not allowed for this location.",
    )
    service = LocationLogbookService(
        session=session,
        storage_service=Mock(),
        location_service=location_service,
    )

    with pytest.raises(HTTPException) as error:
        asyncio.run(
            service.create_police_access_path(
                user_id=7,
                location_id=22,
            )
        )

    assert error.value.status_code == 403
    session.add.assert_not_called()


@pytest.mark.parametrize(
    ("permit", "expected_status"),
    [
        (None, 404),
        (
            SimpleNamespace(
                location_id=11,
                location=SimpleNamespace(name="Central"),
                expires_at=datetime.now() - timedelta(seconds=1),
            ),
            403,
        ),
    ],
)
def test_police_access_rejects_invalid_or_expired_token(
    permit,
    expected_status,
):
    session = AsyncMock()
    result = Mock()
    result.scalar_one_or_none.return_value = permit
    session.execute.return_value = result
    service = LocationLogbookService(
        session=session,
        storage_service=Mock(),
        location_service=AsyncMock(),
    )

    with pytest.raises(HTTPException) as error:
        asyncio.run(service.view_logs_police("invalid-or-expired"))

    assert error.value.status_code == expected_status
    session.delete.assert_not_awaited()
    session.commit.assert_not_awaited()
