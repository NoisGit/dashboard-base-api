"""HTTP security controls shared by the Locentr API."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict, deque
from time import monotonic
from uuid import uuid4

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from src.api.error_contract import error_response
from src.config.config import settings

logger = logging.getLogger(__name__)

RATE_LIMITED_PATHS = {
    "/api/v1/auth/login",
    "/api/v1/auth/operator-login",
    "/api/v1/auth/forgot-password",
    "/api/v1/auth/reset-password",
    "/api/v1/subscriptions/trial",
    "/api/v1/teams/invitations/accept",
    "/api/v1/lifecycle/verify-email",
}
CAPACITY_EXEMPT_PATHS = {"/health", "/live", "/ready"}


class SecurityMiddleware(BaseHTTPMiddleware):
    """Apply basic abuse controls and secure response headers."""

    def __init__(self, app) -> None:
        super().__init__(app)
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()
        self._capacity_lock = asyncio.Lock()
        self._active_requests = 0

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = request.headers.get("x-request-id") or uuid4().hex
        request.state.request_id = request_id
        started_at = monotonic()

        capacity_acquired = request.url.path in CAPACITY_EXEMPT_PATHS
        if not capacity_acquired:
            capacity_acquired = await self._try_acquire_capacity()
            if not capacity_acquired:
                response = self._json_error(
                    status.HTTP_503_SERVICE_UNAVAILABLE,
                    "Service is at capacity. Retry shortly.",
                    request_id,
                )
                response.headers["Retry-After"] = "1"
                return response

        try:
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    if int(content_length) > settings.max_request_body_bytes:
                        return self._json_error(
                            status.HTTP_413_CONTENT_TOO_LARGE,
                            "Request body is too large.",
                            request_id,
                        )
                except ValueError:
                    return self._json_error(
                        status.HTTP_400_BAD_REQUEST,
                        "Invalid Content-Length header.",
                        request_id,
                    )

            if request.method == "POST" and request.url.path in RATE_LIMITED_PATHS:
                retry_after = await self._check_rate_limit(request)
                if retry_after is not None:
                    response = self._json_error(
                        status.HTTP_429_TOO_MANY_REQUESTS,
                        "Too many authentication attempts.",
                        request_id,
                    )
                    response.headers["Retry-After"] = str(retry_after)
                    return response

            response = await call_next(request)
            self._set_security_headers(response, request_id)
            duration_ms = round((monotonic() - started_at) * 1000, 2)
            log_method = (
                logger.warning
                if duration_ms >= settings.slow_request_threshold_ms
                else logger.info
            )
            log_method(
                "request_completed method=%s path=%s status=%s "
                "duration_ms=%s request_id=%s",
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
                request_id,
            )
            return response
        finally:
            if request.url.path not in CAPACITY_EXEMPT_PATHS and capacity_acquired:
                await self._release_capacity()

    async def _try_acquire_capacity(self) -> bool:
        async with self._capacity_lock:
            if self._active_requests >= settings.max_concurrent_requests:
                return False
            self._active_requests += 1
            return True

    async def _release_capacity(self) -> None:
        async with self._capacity_lock:
            self._active_requests = max(0, self._active_requests - 1)

    async def _check_rate_limit(self, request: Request) -> int | None:
        client_host = request.client.host if request.client else "unknown"
        key = f"{client_host}:{request.url.path}"
        now = monotonic()
        window = settings.auth_rate_limit_window_seconds

        async with self._lock:
            timestamps = self._requests[key]
            while timestamps and timestamps[0] <= now - window:
                timestamps.popleft()
            if len(timestamps) >= settings.auth_rate_limit_requests:
                return max(1, int(window - (now - timestamps[0])))
            timestamps.append(now)
        return None

    @staticmethod
    def _set_security_headers(response: Response, request_id: str) -> None:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )
        response.headers["X-Request-ID"] = request_id

    @classmethod
    def _json_error(
        cls,
        status_code: int,
        detail: str,
        request_id: str,
    ) -> JSONResponse:
        response = error_response(
            status_code=status_code,
            message=detail,
            request_id=request_id,
        )
        cls._set_security_headers(response, request_id)
        return response
