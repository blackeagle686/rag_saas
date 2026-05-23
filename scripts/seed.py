"""
Seed script for local development.

Creates a test tenant and API key so you can immediately
start testing the API endpoints.

Usage:
    python -m scripts.seed
"""

from __future__ import annotations

import asyncio
import sys

from api.config import get_settings
from core.security import generate_api_key
from db.engine import async_session_factory
from db.models.tenant import Tenant, TenantPlan, TenantStatus
from db.repositories.api_key_repo import ApiKeyRepository
from db.repositories.tenant_repo import TenantRepository


async def seed() -> None:
    """Create a test tenant and API key."""
    settings = get_settings()

    print("🌱 Seeding database...")
    print(f"   Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else settings.database_url}")

    async with async_session_factory() as session:
        tenant_repo = TenantRepository(session)
        key_repo = ApiKeyRepository(session)

        # Check if test tenant already exists
        existing = await tenant_repo.get_by_email("test@ragaas.dev")
        if existing:
            print("   ✓ Test tenant already exists. Skipping seed.")
            return

        # Create test tenant
        tenant = await tenant_repo.create(
            name="Test Tenant",
            email="test@ragaas.dev",
            plan=TenantPlan.GROWTH,
        )
        print(f"   ✓ Created tenant: {tenant.name} ({tenant.email})")
        print(f"     ID: {tenant.id}")
        print(f"     Plan: {tenant.plan}")

        # Create API key
        raw_key, key_hash, prefix = generate_api_key(settings.api_key_prefix)
        api_key = await key_repo.create(
            tenant_id=tenant.id,
            key_hash=key_hash,
            prefix=prefix,
            label="dev-test-key",
        )

        await session.commit()

        print(f"\n   ✓ Created API key:")
        print(f"     Prefix: {prefix}")
        print(f"     Label: dev-test-key")
        print(f"\n   ╔{'═' * 60}╗")
        print(f"   ║  YOUR API KEY (save this — it won't be shown again!):   ║")
        print(f"   ║  {raw_key:<58} ║")
        print(f"   ╚{'═' * 60}╝")
        print(f"\n   Test with:")
        print(f'   curl -H "Authorization: Bearer {raw_key}" http://localhost:8000/health')
        print(f"\n🌱 Seed complete!")


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
