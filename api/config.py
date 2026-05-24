"""
Application configuration loaded from environment variables.

Uses pydantic-settings for validation, type coercion, and
.env file loading.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the RAGaaS application."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # == Application ==
    app_name: str = "ragaas"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # == API Server ==
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1

    # == PostgreSQL ==
    database_url: str = "postgresql+asyncpg://ragaas:ragaas_secret@localhost:5432/ragaas"
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # == Redis ==
    redis_url: str = "redis://localhost:6379/0"

    # == Qdrant ==
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: str | None = None

    # == OpenAI (Embeddings) ==
    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # == LLM ==
    llm_provider: str = "openai"  # openai | anthropic | mock
    openai_llm_model: str = "gpt-4o"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    mock_llm: bool = False

    # == Storage ==
    storage_backend: str = "local"  # local | s3
    s3_bucket_name: str = "ragaas-files"
    s3_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    local_storage_path: str = "./storage"

    # == Celery ==
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # == Security ==
    api_key_prefix: str = "rgs_live_"
    cors_origins: list[str] = Field(default=["http://localhost:3000"])

    # == Rate Limits (requests per second by plan) ==
    rate_limit_starter: int = 10
    rate_limit_growth: int = 50
    rate_limit_scale: int = 200
    rate_limit_enterprise: int = 500

    # == Ingestion Limits ==
    max_file_size_mb: int = 50
    max_query_length: int = 2000
    chunk_size_tokens: int = 512
    chunk_overlap_tokens: int = 50
    embedding_batch_size: int = 100

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    def get_rate_limit(self, plan: str) -> int:
        """Get rate limit (req/sec) for a plan tier."""
        limits = {
            "starter": self.rate_limit_starter,
            "growth": self.rate_limit_growth,
            "scale": self.rate_limit_scale,
            "enterprise": self.rate_limit_enterprise,
        }
        return limits.get(plan, self.rate_limit_starter)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
