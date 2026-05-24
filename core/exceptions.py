"""
Custom exception classes for RAGaaS.

All API exceptions inherit from RAGaaSError and carry
an HTTP status code + machine-readable error code for
consistent JSON error responses.
"""

from __future__ import annotations

from typing import Any


class RAGaaSError(Exception):
    """Base exception for all RAGaaS errors."""

    status_code: int = 500
    error_code: str = "internal_error"
    detail: str = "An unexpected error occurred."

    def __init__(self, detail: str | None = None, **kwargs: Any) -> None:
        self.detail = detail or self.__class__.detail
        self.extra = kwargs
        super().__init__(self.detail)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "error": {
                "code": self.error_code,
                "message": self.detail,
            }
        }
        if self.extra:
            payload["error"]["details"] = self.extra
        return payload


# == Authentication ==


class InvalidAPIKeyError(RAGaaSError):
    status_code = 401
    error_code = "invalid_api_key"
    detail = "The provided API key is invalid or has been revoked."


class MissingAPIKeyError(RAGaaSError):
    status_code = 401
    error_code = "missing_api_key"
    detail = "Authorization header with a valid API key is required."


# == Rate Limiting ==


class RateLimitExceededError(RAGaaSError):
    status_code = 429
    error_code = "rate_limit_exceeded"
    detail = "Rate limit exceeded. Please retry after the specified time."

    def __init__(self, retry_after: int = 1, **kwargs: Any) -> None:
        self.retry_after = retry_after
        super().__init__(**kwargs)


# == Resource Errors ==


class NotFoundError(RAGaaSError):
    status_code = 404
    error_code = "not_found"
    detail = "The requested resource was not found."


class ConflictError(RAGaaSError):
    status_code = 409
    error_code = "conflict"
    detail = "A resource with that identifier already exists."


# == Validation ==


class ValidationError(RAGaaSError):
    status_code = 422
    error_code = "validation_error"
    detail = "The request body contains invalid data."


class FileTooLargeError(RAGaaSError):
    status_code = 413
    error_code = "file_too_large"
    detail = "The uploaded file exceeds the maximum size of 50MB."


class UnsupportedFileTypeError(RAGaaSError):
    status_code = 415
    error_code = "unsupported_file_type"
    detail = "The uploaded file type is not supported."


# == Authorization ==


class TenantSuspendedError(RAGaaSError):
    status_code = 403
    error_code = "tenant_suspended"
    detail = "Your account has been suspended. Please contact support."


class PlanLimitExceededError(RAGaaSError):
    status_code = 402
    error_code = "plan_limit_exceeded"
    detail = "You have exceeded your plan's usage limits. Please upgrade."


# == Service Errors ==


class ExternalServiceError(RAGaaSError):
    status_code = 502
    error_code = "external_service_error"
    detail = "An external service is temporarily unavailable."


class IngestionError(RAGaaSError):
    status_code = 500
    error_code = "ingestion_error"
    detail = "An error occurred during document ingestion."
