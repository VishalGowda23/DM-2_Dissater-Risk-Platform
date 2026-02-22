#!/usr/bin/env python3
"""Test remaining endpoints with correct URLs."""
import requests, json

BASE = "http://localhost:8000"

def test(name, method, url, json_data=None, timeout=10):
    print(f"\n{'='*60}")
    print(f"FEATURE: {name}")
    print(f"  {method} {url}")
    try:
        if method == "GET":
            r = requests.get(f"{BASE}{url}", timeout=timeout)
        else:
            r = requests.post(f"{BASE}{url}", json=json_data, timeout=timeout)
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            d = r.json()
            if isinstance(d, dict):
                print(f"  Keys: {sorted(d.keys())}")
                for k, v in d.items():
                    s = json.dumps(v, default=str)
                    if len(s) > 200:
                        s = s[:200] + "..."
                    print(f"    {k}: {s}")
            elif isinstance(d, list):
                print(f"  List length: {len(d)}")
                if d:
                    print(f"  First item: {json.dumps(d[0], default=str)[:200]}")
        else:
            print(f"  Body: {r.text[:500]}")
    except Exception as e:
        print(f"  ERROR: {e}")

# Corrected URLs
test("Decision Support", "GET", "/api/decision-support")
test("Resource Optimizer", "POST", "/api/optimize", {
    "budget": 1000000,
    "priority": "flood"
})
test("Calculate Risks", "POST", "/api/calculate-risks")
test("Historical Validate", "POST", "/api/historical/validate/pune_2019_sep")
test("Cascading Chains", "GET", "/api/cascading/chains")
test("Cascading Evaluate", "POST", "/api/cascading/evaluate", {
    "chain_id": "cascade_001",
    "trigger_ward": "W003",
    "event_type": "flood",
    "intensity": 0.7
})

# Also check scenario response structure more carefully
test("Scenario (detailed)", "POST", "/api/scenario", {
    "rainfall_mm": 120,
    "duration_hours": 6,
    "affected_wards": ["W003", "W005"]
})

print("\nDONE!")
