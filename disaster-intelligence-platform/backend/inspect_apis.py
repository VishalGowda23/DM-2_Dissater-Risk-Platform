#!/usr/bin/env python3
"""Inspect API responses to identify issues."""
import requests, json, sys

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
                    if len(s) > 150:
                        s = s[:150] + "..."
                    print(f"    {k}: {s}")
            elif isinstance(d, list):
                print(f"  List length: {len(d)}")
                if d:
                    print(f"  First item keys: {sorted(d[0].keys()) if isinstance(d[0], dict) else 'N/A'}")
                    s = json.dumps(d[0], default=str)
                    if len(s) > 200:
                        s = s[:200] + "..."
                    print(f"  First item: {s}")
        else:
            print(f"  Body: {r.text[:300]}")
    except requests.exceptions.Timeout:
        print(f"  TIMEOUT after {timeout}s!")
    except Exception as e:
        print(f"  ERROR: {e}")

# 1. Ward API - check for centroid
print("="*60)
print("INVESTIGATING ISSUES")
print("="*60)

test("Wards (centroid check)", "GET", "/api/wards?page_size=2")

# 2. Risk Explanation - surge_level
test("Risk Explain (surge_level)", "GET", "/api/risk/explain/W003")

# 3. Weather/Forecast endpoint
test("Forecast per ward", "GET", "/api/forecast/W003")
test("Forecast all", "GET", "/api/forecast")

# 4. Scenario
test("Scenario", "POST", "/api/scenario", {
    "rainfall_mm": 120,
    "duration_hours": 6,
    "affected_wards": ["W003"]
})

# 5. Historical
test("Historical events", "GET", "/api/historical/events")
test("Historical validation", "GET", "/api/historical/validation")

# 6. River monitor
test("River monitor", "GET", "/api/rivers", timeout=5)

# 7. Cascading evaluate
test("Cascading evaluate", "POST", "/api/cascading/evaluate", {
    "trigger_ward": "W003",
    "event_type": "flood",
    "intensity": 0.7
})

# 8. Alerts
test("Alerts", "GET", "/api/alerts")

# 9. Evacuation
test("Evacuation ward", "GET", "/api/evacuation/W003")
test("Evacuation all", "GET", "/api/evacuation")

# 10. Decision support
test("Decision support", "GET", "/api/decision/support")

# 11. Resource optimizer
test("Resource optimizer", "POST", "/api/resources/optimize", {
    "budget": 1000000,
    "priority": "flood"
})

# 12. Shelters
test("Shelters", "GET", "/api/shelters")

# 13. Calculate risks trigger
test("Calculate risks", "POST", "/api/risk/calculate")

print("\n\nDONE!")
