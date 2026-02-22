import asyncio
import httpx

BASE = "http://localhost:8000"


async def test():
    async with httpx.AsyncClient(timeout=60.0) as c:
        # historical validate - POST
        r = await c.post(f"{BASE}/api/historical/validate/pune_flood_2019")
        if r.status_code == 200:
            d = r.json()
            print(f"historical validate: 200 keys={list(d.keys())}")
        else:
            print(f"historical validate: {r.status_code} {r.text[:200]}")

        # cascade evaluate - POST with chain_id
        r = await c.post(f"{BASE}/api/cascading/evaluate", json={"chain_id": "dam_breach_cascade"})
        if r.status_code == 200:
            d = r.json()
            print(f"cascade evaluate: 200 keys={list(d.keys())}")
        else:
            print(f"cascade evaluate: {r.status_code} {r.text[:200]}")

        # optimize - POST
        r = await c.post(f"{BASE}/api/optimize", json={})
        if r.status_code == 200:
            d = r.json()
            print(f"optimize: 200 keys={list(d.keys())}")
        else:
            print(f"optimize: {r.status_code} {r.text[:200]}")


asyncio.run(test())
