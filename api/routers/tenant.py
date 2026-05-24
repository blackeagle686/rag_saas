"""
Tenant router.

Endpoints for managing tenant-specific settings and configurations.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.middleware.auth import get_current_tenant
from api.schemas.tenant import TenantSettingsResponse, TenantSettingsUpdate
from db.engine import get_db_session
from db.models.tenant import Tenant
from db.repositories.tenant_repo import TenantRepository

router = APIRouter(prefix="/v1/tenant", tags=["Tenant"])


@router.get(
    "/settings",
    response_model=TenantSettingsResponse,
    summary="Get tenant settings",
    description="Get the custom LLM configurations (model, provider, base URL, API key) for the current tenant.",
)
async def get_tenant_settings(
    tenant: Tenant = Depends(get_current_tenant),
) -> TenantSettingsResponse:
    """Get the custom LLM settings for the authenticated tenant."""
    return TenantSettingsResponse.from_tenant(tenant)


@router.patch(
    "/settings",
    response_model=TenantSettingsResponse,
    summary="Update tenant settings",
    description="Update the custom LLM configurations (model, provider, base URL, API key) for the current tenant.",
)
async def update_tenant_settings(
    payload: TenantSettingsUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db_session),
) -> TenantSettingsResponse:
    """Update the custom LLM settings for the authenticated tenant."""
    tenant_repo = TenantRepository(db)

    # Only update fields that were explicitly provided
    provider = payload.llm_provider if payload.llm_provider is not None else tenant.llm_provider
    model = payload.llm_model if payload.llm_model is not None else tenant.llm_model
    api_key = payload.llm_api_key if payload.llm_api_key is not None else tenant.llm_api_key
    base_url = payload.llm_base_url if payload.llm_base_url is not None else tenant.llm_base_url

    updated_tenant = await tenant_repo.update_llm_settings(
        tenant_id=tenant.id,
        llm_provider=provider,
        llm_model=model,
        llm_api_key=api_key,
        llm_base_url=base_url,
    )
    await db.commit()

    return TenantSettingsResponse.from_tenant(updated_tenant)
