"""
Tenant settings schemas.

Defines the API structures for managing custom LLM settings.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TenantSettingsResponse(BaseModel):
    llm_provider: str = Field(..., description="LLM provider (e.g., openai, anthropic)")
    llm_model: str = Field(..., description="Model name to use")
    llm_api_key: str = Field(..., description="API key (masked for security)")
    llm_base_url: str = Field(..., description="Base URL of the LLM endpoint")

    class Config:
        from_attributes = True

    @classmethod
    def from_tenant(cls, tenant) -> TenantSettingsResponse:
        """Helper to create a response with a masked API key."""
        key = tenant.llm_api_key or ""
        masked_key = ""
        if key:
            if len(key) > 10:
                masked_key = f"{key[:6]}...{key[-4:]}"
            else:
                masked_key = "********"
        return cls(
            llm_provider=tenant.llm_provider,
            llm_model=tenant.llm_model,
            llm_api_key=masked_key,
            llm_base_url=tenant.llm_base_url,
        )


class TenantSettingsUpdate(BaseModel):
    llm_provider: str | None = Field(None, min_length=1, max_length=50, description="LLM provider (e.g., openai)")
    llm_model: str | None = Field(None, min_length=1, max_length=100, description="Model name to use")
    llm_api_key: str | None = Field(None, min_length=1, max_length=255, description="API key to set")
    llm_base_url: str | None = Field(None, min_length=1, max_length=255, description="Base URL of the LLM endpoint")
