import asyncio
import httpx

async def verify():
    base_url = "http://localhost:8000/api/dev"
    
    print("1. Resetting ironmarch-001 encounter...")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{base_url}/reset-encounter/ironmarch-001")
            print(f"   Response: {resp.status_code} - {resp.json()}")
        except Exception as e:
            print(f"   Error resetting encounter: {e}")

        print("\n2. Loading seeds with overwrite=true...")
        try:
            resp = await client.post(f"{base_url}/load-seeds?overwrite=true")
            print(f"   Response: {resp.status_code}")
            # print(f"   Summary: {resp.json().get('summary')}")
        except Exception as e:
            print(f"   Error loading seeds: {e}")

    print("\nVerification steps sent to backend server.")

if __name__ == "__main__":
    asyncio.run(verify())
