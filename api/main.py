"""
FastAPI application factory and lifespan management.

Creates the main application with all routers, middleware,
exception handlers, and lifespan events.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.config import get_settings
from api.middleware.audit_log import AuditLogMiddleware
from api.middleware.security_headers import SecurityHeadersMiddleware
from api.routers import health, keys, namespaces, ingest, query, tenant
from api.routers.namespaces import documents_router
from core.exceptions import RAGaaSError, RateLimitExceededError
from core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown events."""
    settings = get_settings()

    # Setup structured logging
    setup_logging(
        log_level=settings.log_level,
        json_output=settings.is_production,
    )

    # Create local storage directory
    if settings.storage_backend == "local":
        from pathlib import Path

        Path(settings.local_storage_path).mkdir(parents=True, exist_ok=True)

    yield

    # Shutdown: close database engine
    from db.engine import engine

    await engine.dispose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="RAGaaS API",
        description=(
            "RAG-as-a-Service — Add intelligent document search and Q&A "
            "to your product in minutes. Upload documents, ask questions, "
            "get answers with source references."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # == Exception Handlers ==

    @app.exception_handler(RAGaaSError)
    async def ragaas_error_handler(request: Request, exc: RAGaaSError) -> JSONResponse:
        """Handle all custom RAGaaS exceptions with consistent JSON format."""
        headers = {}
        if isinstance(exc, RateLimitExceededError):
            headers["Retry-After"] = str(exc.retry_after)

        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
            headers=headers,
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        """Catch-all for unhandled exceptions — never leak internals."""
        from core.logging import get_logger

        logger = get_logger("error_handler")
        logger.error("unhandled_exception", error=str(exc), exc_info=True)

        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "An unexpected error occurred. Please try again later.",
                }
            },
        )

    # == Middleware (order matters: last added = first executed) ==

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-RateLimit-Remaining", "X-RateLimit-Limit"],
    )

    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # Audit logging
    app.add_middleware(AuditLogMiddleware)

    # == Routers ==

    app.include_router(health.router)
    app.include_router(keys.router)
    app.include_router(namespaces.router)
    app.include_router(documents_router)
    app.include_router(ingest.router)
    app.include_router(query.router)
    app.include_router(tenant.router)

    return app


# Create the application instance
app = create_app()
