import httpx
import asyncio

API_KEY = "rgs_live_KVZoG7klMm25HiuZBAYneNWzqLVETAOJ"
BASE_URL = "http://localhost:8000"

async def test():
    headers = {"Authorization": f"Bearer {API_KEY}"}
    async with httpx.AsyncClient() as client:
        # 1. Get initial settings
        print("1. Fetching initial settings...")
        r = await client.get(f"{BASE_URL}/v1/tenant/settings", headers=headers)
        print("Status:", r.status_code)
        print("Response:", r.json())
        assert r.status_code == 200
        
        # 2. Update settings to Anthropic / custom
        print("\n2. Updating settings to custom LLM configuration...")
        update_data = {
            "llm_provider": "anthropic",
            "llm_model": "claude-3-5-sonnet-20241022",
            "llm_api_key": "sk-ant-api03-abcdef-123456",
            "llm_base_url": "https://api.anthropic.com"
        }
        r = await client.patch(f"{BASE_URL}/v1/tenant/settings", json=update_data, headers=headers)
        print("Status:", r.status_code)
        print("Response:", r.json())
        assert r.status_code == 200
        
        # 3. Fetch again to verify updates and key masking
        print("\n3. Fetching settings again to verify values...")
        r = await client.get(f"{BASE_URL}/v1/tenant/settings", headers=headers)
        print("Status:", r.status_code)
        data = r.json()
        print("Response:", data)
        assert data["llm_provider"] == "anthropic"
        assert data["llm_model"] == "claude-3-5-sonnet-20241022"
        assert data["llm_api_key"] == "sk-ant...3456"  # masked key representation
        assert data["llm_base_url"] == "https://api.anthropic.com"
        
        # 4. Let's do a RAG query to verify local embedding & LLM service logic
        # We need a namespace. Let's list namespaces first.
        print("\n4. Listing namespaces...")
        r = await client.get(f"{BASE_URL}/v1/namespaces", headers=headers)
        print("Status:", r.status_code)
        namespaces = r.json()
        print("Namespaces:", namespaces)
        
        ns_list = namespaces.get("namespaces", [])
        if ns_list:
            ns_name = ns_list[0]["name"]
            print(f"\n5. Performing RAG query on namespace {ns_name}...")
            query_data = {
                "namespace": ns_name,
                "query": "hello, test custom LLM settings",
                "top_k": 3,
                "model": "claude-3-5-sonnet-20241022"
            }
            r = await client.post(f"{BASE_URL}/v1/query", json=query_data, headers=headers)
            print("Query Status:", r.status_code)
            print("Query Response:", r.json())

if __name__ == "__main__":
    asyncio.run(test())
