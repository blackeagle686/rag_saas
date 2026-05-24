import asyncio
from db.engine import async_session_factory
from db.repositories.tenant_repo import TenantRepository
from db.repositories.api_key_repo import ApiKeyRepository
from core.security import generate_api_key
from api.config import get_settings

async def main():
    settings = get_settings()
    async with async_session_factory() as session:
        t_repo = TenantRepository(session)
        k_repo = ApiKeyRepository(session)
        tenant = await t_repo.get_by_email("test@ragaas.dev")
        if not tenant:
            print("No tenant found!")
            return
        raw_key, key_hash, prefix = generate_api_key(settings.api_key_prefix)
        await k_repo.create(
            tenant_id=tenant.id,
            key_hash=key_hash,
            prefix=prefix,
            label="temporary-run-key",
        )
        await session.commit()
        print(f"RAW_KEY: {raw_key}")

if __name__ == "__main__":
    asyncio.run(main())
