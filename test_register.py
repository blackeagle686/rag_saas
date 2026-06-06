import asyncio
from httpx import AsyncClient, ASGITransport
from api.main import app

async def test():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/v1/auth/register", json={
            "name": "Test User",
            "email": "testuser2@example.com",
            "password": "strongpassword"
        })
        print(response.status_code, response.json())

asyncio.run(test())
