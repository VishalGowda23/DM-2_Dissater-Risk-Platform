#!/usr/bin/env python3
"""Debug optimizer vs risk score ordering."""
import requests, json

BASE = "http://localhost:8000"

# Get risk scores
r = requests.get(f"{BASE}/api/risk")
d = r.json()
risk = sorted(d["risk_data"], key=lambda x: x["top_risk_score"])

print("=== RISK SCORES (lowest to highest) ===")
for w in risk[:5]:
    print(f"  {w['ward_id']} {w['ward_name']:20s} risk={w['top_risk_score']:5.1f}")
print("  ...")
for w in risk[-5:]:
    print(f"  {w['ward_id']} {w['ward_name']:20s} risk={w['top_risk_score']:5.1f}")

# Get optimizer results
r2 = requests.post(f"{BASE}/api/optimize", json={"scenario": {"use_delta": True}})
d2 = r2.json()
allocs = d2["ward_allocations"]

print("\n=== OPTIMIZER ALLOCATIONS (sorted by need, top 10) ===")
for a in allocs[:10]:
    total = sum(v.get("allocated", 0) for v in a.get("resources", {}).values())
    ns = a.get("need_score", "?")
    rs = a.get("combined_risk", a.get("risk_score", "?"))
    print(f"  {a['ward_id']} {a.get('ward_name','?'):20s} combined_risk={rs:>5} need={ns:>6} alloc={total}")

print("\n=== OPTIMIZER BOTTOM 5 ===")
for a in allocs[-5:]:
    total = sum(v.get("allocated", 0) for v in a.get("resources", {}).values())
    ns = a.get("need_score", "?")
    rs = a.get("combined_risk", a.get("risk_score", "?"))
    print(f"  {a['ward_id']} {a.get('ward_name','?'):20s} combined_risk={rs:>5} need={ns:>6} alloc={total}")

print(f"\nHighest need ward: {d2['summary']['highest_need_ward']}")
print(f"Lowest need ward: {d2['summary'].get('lowest_need_ward', 'N/A')}")

# Show full first allocation
print("\n=== FIRST ALLOCATION DETAIL ===")
print(json.dumps(allocs[0], indent=2, default=str))

# Show explanations
print("\n=== EXPLANATIONS ===")
print(json.dumps(d2.get("explanations", {}), indent=2, default=str)[:600])
