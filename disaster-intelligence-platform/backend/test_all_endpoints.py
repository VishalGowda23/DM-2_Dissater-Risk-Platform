"""Quick API endpoint validation"""
import asyncio
import httpx
import json

BASE = "http://localhost:8000"

ENDPOINTS = [
    ("GET", "/health", None),
    ("GET", "/api/wards", None),
    ("GET", "/api/risk", None),
    ("GET", "/api/risk/summary", None),
    ("GET", "/api/risk/explain/W001", None),
    ("GET", "/api/scenarios", None),
    ("POST", "/api/scenario/run", {"scenario_type": "heavy_rain", "params": {"rainfall_mm": 150, "duration_hours": 6, "intensity": "heavy"}}),
    ("GET", "/api/forecast", None),
    ("GET", "/api/forecast/W001", None),
    ("GET", "/api/historical/events", None),
    ("GET", "/api/historical/validate/pune_flood_2019", None),
    ("GET", "/api/rivers", None),
    ("GET", "/api/rivers/impact", None),
    ("GET", "/api/cascading/chains", None),
    ("POST", "/api/cascading/evaluate", {"trigger_type": "dam_release", "params": {"volume_mcft": 15}}),
    ("GET", "/api/alerts", None),
    ("GET", "/api/shelters", None),
    ("GET", "/api/evacuation/W001", None),
    ("GET", "/api/decision-support", None),
    ("GET", "/api/optimize", None),
]


async def main():
    async with httpx.AsyncClient(timeout=60.0) as client:
        for method, path, body in ENDPOINTS:
            try:
                if method == "GET":
                    r = await client.get(f"{BASE}{path}")
                else:
                    r = await client.post(f"{BASE}{path}", json=body)
                d = r.json()
                keys = list(d.keys()) if isinstance(d, dict) else f"[list:{len(d)}]"
                status = "\u2705" if r.status_code == 200 else f"\u274c {r.status_code}"
                print(f"{status} {method:4s} {path:40s} keys={keys}")
            except Exception as e:
                print(f"\u274c {method:4s} {path:40s} ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(main())
