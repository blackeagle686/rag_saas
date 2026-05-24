"""
Audit logging middleware.

Logs every request with tenant context, timing,
and response status for security auditing.
"""

from __future__ import annotations

import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger("audit")


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Log every API request for security auditing and debugging."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Record start time
        start_time = time.perf_counter()

        # Get client IP (respect proxy headers)
        client_ip = request.headers.get(
            "X-Forwarded-For", request.client.host if request.client else "unknown"
        )

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            # Log failed requests
            tenant_id = getattr(request.state, "tenant_id", None)
            if tenant_id is None:
                tenant = getattr(request.state, "tenant", None)
                if tenant:
                    try:
                        tenant_id = tenant.id
                    except Exception:
                        pass
            logger.error(
                "request_failed",
                request_id=request_id,
                tenant_id=str(tenant_id) if tenant_id else None,
                method=request.method,
                path=request.url.path,
                client_ip=client_ip,
                duration_ms=duration_ms,
            )
            raise

        # Calculate duration
        duration_ms = int((time.perf_counter() - start_time) * 1000)

        # Extract tenant info if available
        tenant_id = getattr(request.state, "tenant_id", None)
        if tenant_id is None:
            tenant = getattr(request.state, "tenant", None)
            if tenant:
                try:
                    tenant_id = tenant.id
                except Exception:
                    pass
        tenant_id_str = str(tenant_id) if tenant_id else None

        # Determine log level
        log_level = "info"
        if response.status_code >= 500:
            log_level = "error"
        elif response.status_code >= 400:
            log_level = "warning"
        elif duration_ms > 2000:
            log_level = "warning"

        # Build log entry
        log_data = {
            "request_id": request_id,
            "tenant_id": tenant_id_str,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "client_ip": client_ip,
            "user_agent": request.headers.get("user-agent", ""),
        }

        # Log at appropriate level
        getattr(logger, log_level)("api_request", **log_data)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response
