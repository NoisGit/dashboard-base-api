"""Versioned API error responses with legacy detail compatibility."""

import logging
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)
ERROR_VERSION = "1"

STATUS_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    413: "payload_too_large",
    422: "validation_error",
    429: "rate_limited",
    500: "internal_error",
    502: "provider_error",
    503: "service_unavailable",
}


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", uuid4().hex)


def error_response(
    *,
    status_code: int,
    message: str,
    request_id: str,
    code: str | None = None,
    details: Any = None,
) -> JSONResponse:
    """Build the v1 envelope while retaining `detail` for old clients."""
    response = JSONResponse(
        status_code=status_code,
        content={
            "version": ERROR_VERSION,
            "code": code or STATUS_CODES.get(status_code, "request_failed"),
            "message": message,
            "details": details,
            "request_id": request_id,
            "detail": message,
        },
    )
    response.headers["X-Request-ID"] = request_id
    return response


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    detail = exc.detail
    message = detail if isinstance(detail, str) else "Request could not be completed."
    details = None if isinstance(detail, str) else detail
    return error_response(
        status_code=exc.status_code,
        message=message,
        request_id=_request_id(request),
        details=details,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    details = [
        {
            "field": ".".join(str(value) for value in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]
    return error_response(
        status_code=422,
        code="validation_error",
        message="Request validation failed.",
        request_id=_request_id(request),
        details=details,
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    request_id = _request_id(request)
    logger.exception(
        "unhandled_request_error path=%s request_id=%s",
        request.url.path,
        request_id,
    )
    return error_response(
        status_code=500,
        code="internal_error",
        message="The service could not complete the request.",
        request_id=request_id,
    )


OPENAPI_ERROR_EXAMPLE = {
    "version": "1",
    "code": "validation_error",
    "message": "Request validation failed.",
    "details": [
        {
            "field": "body.email",
            "message": "value is not a valid email address",
            "type": "value_error",
        }
    ],
    "request_id": "b9c22fa65ec54acba27dfcc8fe13df33",
    "detail": "Request validation failed.",
}
