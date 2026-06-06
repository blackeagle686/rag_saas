import asyncio
from db.engine import engine
from db.models.base import Base

# Import all models to ensure they are registered with Base.metadata
from db.models import tenant, namespace, document, api_key, usage_event

async def reset():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        print("Dropped all tables.")
        await conn.run_sync(Base.metadata.create_all)
        print("Created all tables.")

asyncio.run(reset())
