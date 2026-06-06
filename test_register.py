import asyncio
from httpx import AsyncClient
from api.main import app

async def test():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/v1/auth/register", json={
            "name": "Test User",
            "email": "testuser@example.com",
            "password": "strongpassword"
        })
        print(response.status_code, response.json())

asyncio.run(test())
