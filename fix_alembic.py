import asyncio
from sqlalchemy import text
from db.engine import engine

async def fix():
    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version"))

asyncio.run(fix())
