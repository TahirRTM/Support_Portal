"""Application exception hierarchy and a consistent error envelope.

Stack traces are never returned to clients. Every handled error maps to a
stable machine-readable ``code`` plus a safe human message.
"""
from __future__ import annotations

from fastapi import Request, status
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = "app_error"
    message: str = "Request could not be processed."

    def __init__(self, message: str | None = None, *, code: str | None = None,
                 status_code: int | None = None, extra: dict | None = None) -> None:
        super().__init__(message or self.message)
        if message:
            self.message = message
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code
        self.extra = extra or {}


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"
    message = "Resource not found."


class ValidationError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    code = "validation_error"
    message = "Invalid input."


class AuthError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "authentication_failed"
    # Deliberately generic to avoid user/credential enumeration.
    message = "Authentication failed."


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "forbidden"
    message = "You do not have access to this resource."


class RateLimitError(AppError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    code = "rate_limited"
    message = "Too many requests. Please try again later."

    def __init__(self, retry_after: int, message: str | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class CaptchaError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "captcha_failed"
    message = "CAPTCHA verification failed."


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "conflict"
    message = "Resource conflict."


def _envelope(code: str, message: str, request: Request, extra: dict | None = None) -> dict:
    body = {
        "error": {
            "code": code,
            "message": message,
            "request_id": getattr(request.state, "request_id", None),
        }
    }
    if extra:
        body["error"]["details"] = extra
    return body


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    headers = {}
    if isinstance(exc, RateLimitError):
        headers["Retry-After"] = str(exc.retry_after)
    return JSONResponse(
        status_code=exc.status_code,
        content=_envelope(exc.code, exc.message, request, exc.extra or None),
        headers=headers,
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    # Never leak internals. The real error is logged with the request id upstream.
    return JSONResponse(
        status_code=500,
        content=_envelope("internal_error", "An unexpected error occurred.", request),
    )
