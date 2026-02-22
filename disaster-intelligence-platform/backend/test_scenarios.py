"""Test scenario API output"""
import requests, json

BASE = "http://localhost:8000"

tests = [
    ("DEFAULT (all neutral)", {
        "rainfall_multiplier": 1.0,
        "temp_anomaly_addition": 0,
        "drainage_efficiency_multiplier": 1.0,
        "population_growth_pct": 0
    }),
    ("EXTREME RAIN 3x", {
        "rainfall_multiplier": 3.0,
        "temp_anomaly_addition": 0,
        "drainage_efficiency_multiplier": 1.0,
        "population_growth_pct": 0
    }),
    ("HEATWAVE +5C", {
        "rainfall_multiplier": 1.0,
        "temp_anomaly_addition": 5,
        "drainage_efficiency_multiplier": 1.0,
        "population_growth_pct": 0
    }),
    ("BLOCKED DRAINS 0.5x", {
        "rainfall_multiplier": 1.0,
        "temp_anomaly_addition": 0,
        "drainage_efficiency_multiplier": 0.5,
        "population_growth_pct": 0
    }),
    ("COMPOUND: 2x Rain + 3C + 30% pop growth", {
        "rainfall_multiplier": 2.0,
        "temp_anomaly_addition": 3,
        "drainage_efficiency_multiplier": 1.0,
        "population_growth_pct": 30
    }),
]

for label, params in tests:
    r = requests.post(f"{BASE}/api/scenario", json={
        "scenario_key": "custom",
        "custom_params": params,
    })
    d = r.json()
    agg = d["aggregate_impact"]
    
    print(f"=== {label} ===")
    print(f"  Flood Δ: {agg['avg_flood_risk_change']:+.1f}%   Heat Δ: {agg['avg_heat_risk_change']:+.1f}%   Newly critical: {agg['wards_newly_critical']}")
    
    # Show top 3 and bottom 3
    results = d["results"]
    print(f"  Top 3 impacted:")
    for wr in results[:3]:
        b = wr["baseline"]
        s = wr["scenario"]
        ch = s["top_risk_score"] - b["top_risk_score"]
        print(f"    {b['ward_name']:20s} {b['top_risk_score']:5.1f} → {s['top_risk_score']:5.1f}  (Δ={ch:+.1f})")
    
    print(f"  Bottom 3:")
    for wr in results[-3:]:
        b = wr["baseline"]
        s = wr["scenario"]
        ch = s["top_risk_score"] - b["top_risk_score"]
        print(f"    {b['ward_name']:20s} {b['top_risk_score']:5.1f} → {s['top_risk_score']:5.1f}  (Δ={ch:+.1f})")
    print()
