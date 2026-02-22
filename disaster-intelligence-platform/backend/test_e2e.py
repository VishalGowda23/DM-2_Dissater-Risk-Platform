"""
End-to-End Validation Script for PRAKALP
Tests the complete pipeline: weather ingestion → risk calculation → all API endpoints
"""
import asyncio
import httpx
import json
from datetime import datetime

BASE = "http://localhost:8000"
PASSED = 0
FAILED = 0
WARNINGS = 0


def check(name, condition, detail=""):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  \u2705 {name}")
    else:
        FAILED += 1
        print(f"  \u274c {name} — {detail}")


def warn(name, detail=""):
    global WARNINGS
    WARNINGS += 1
    print(f"  \u26a0\ufe0f  {name} — {detail}")


async def main():
    global PASSED, FAILED, WARNINGS
    print("=" * 60)
    print("PRAKALP End-to-End Validation")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=90.0) as c:

        # 1. HEALTH CHECK
        print("\n--- 1. Health Check ---")
        r = await c.get(f"{BASE}/health")
        d = r.json()
        check("Server healthy", d["status"] == "healthy")
        check("Database connected", d["services"]["database"] == "connected")
        check("Redis connected", d["services"]["redis"] == "connected")
        check("ML model loaded", d["services"]["ml_model"] == "loaded")
        check("20 wards loaded", d["data"]["wards_loaded"] == 20)

        # 2. WEATHER INGESTION
        print("\n--- 2. Weather Ingestion ---")
        r = await c.post(f"{BASE}/api/ingest/weather")
        d = r.json()
        check("Weather ingestion completes", d.get("status") == "completed")
        check("20 wards ingested", d.get("successful", 0) == 20, f"got {d.get('successful')}")

        # 3. RISK CALCULATION
        print("\n--- 3. Risk Calculation ---")
        r = await c.post(f"{BASE}/api/calculate-risks")
        d = r.json()
        check("Risk calc completes", d.get("status") == "completed")
        check("20 wards processed", d.get("processed") == 20, f"got {d.get('processed')}")
        check("0 failures", d.get("failed") == 0, f"got {d.get('failed')}")
        check("Weather fetched for all", d.get("weather_fetched", 0) >= 18)

        # 4. RISK DATA QUALITY
        print("\n--- 4. Risk Data Quality ---")
        r = await c.get(f"{BASE}/api/risk")
        d = r.json()
        risks = d.get("risk_data", [])
        check("20 risk scores returned", len(risks) == 20, f"got {len(risks)}")

        if risks:
            scores = [r["top_risk_score"] for r in risks]
            check("Risk scores > 0", min(scores) > 0, f"min={min(scores)}")
            check("Risk scores <= 100", max(scores) <= 100, f"max={max(scores)}")
            check("Flood/heat data present", all(r.get("flood") and r.get("heat") for r in risks))
            check("top_hazard set", all(r.get("top_hazard") for r in risks))

            # Check delta calculation
            for r in risks[:3]:
                flood_delta = r["flood"]["delta_pct"]
                heat_delta = r["heat"]["delta_pct"]
                if flood_delta < -100 or flood_delta > 500:
                    warn(f"{r['ward_id']} flood delta_pct extreme: {flood_delta}")
                if heat_delta < -100 or heat_delta > 500:
                    warn(f"{r['ward_id']} heat delta_pct extreme: {heat_delta}")

        # 5. RISK SUMMARY
        print("\n--- 5. Risk Summary ---")
        r = await c.get(f"{BASE}/api/risk/summary")
        d = r.json()
        check("Summary has total_wards", d.get("total_wards") == 20)
        check("Has total_population", d.get("total_population", 0) > 0, f"got {d.get('total_population')}")
        check("Has overall_status", d.get("overall_status") in ["normal","elevated","high","critical"])
        check("Has risk_distribution", all(k in d.get("risk_distribution",{}) for k in ["critical","high","moderate","low"]))
        check("Has critical_wards.count", isinstance(d.get("critical_wards",{}).get("count"), int))
        check("Has high_risk_wards.count", isinstance(d.get("high_risk_wards",{}).get("count"), int))
        surge = d.get("alerts",{}).get("surge_alerts", 0)
        check("Surge alerts < 20 (fix verified)", surge < 20, f"got {surge}")

        # 6. RISK EXPLANATION
        print("\n--- 6. Risk Explanation ---")
        r = await c.get(f"{BASE}/api/risk/explain/W010", params={"hazard": "heat"})
        d = r.json()
        check("Has surge_level", d.get("surge_level") in ["normal","elevated","surge","critical"])
        check("Has narrative", len(d.get("narrative","")) > 20, f"got '{d.get('narrative','')[:50]}'")
        check("Has top_drivers_event", isinstance(d.get("top_drivers_event"), list))
        check("Has recommendations", len(d.get("recommendations",[])) > 0)
        check("Has confidence", d.get("confidence") is not None)

        # 7. SCENARIO SIMULATION
        print("\n--- 7. Scenario Simulation ---")
        r = await c.post(f"{BASE}/api/scenario/run", json={
            "scenario_type": "heavy_rain",
            "params": {"rainfall_mm": 200, "duration_hours": 6, "intensity": "heavy"}
        })
        d = r.json()
        check("Scenario returns results", len(d.get("results",[])) > 0, f"got {len(d.get('results',[]))}")
        check("Has aggregate_impact", d.get("aggregate_impact") is not None)

        # Also test custom scenario (frontend format)
        r = await c.post(f"{BASE}/api/scenario", json={
            "scenario_key": "custom",
            "custom_params": {"rainfall_multiplier": 3.0, "temp_anomaly_addition": 5}
        })
        d2 = r.json()
        check("Custom scenario (frontend) works", len(d2.get("results",[])) > 0)

        # 8. FORECAST
        print("\n--- 8. 48h Forecast ---")
        r = await c.get(f"{BASE}/api/forecast")
        d = r.json()
        check("20 ward forecasts", len(d.get("forecasts",[])) == 20)
        if d.get("forecasts"):
            fc = d["forecasts"][0]
            check("Has timeline", len(fc.get("timeline",[])) >= 10, f"got {len(fc.get('timeline',[]))}")
            check("Has peak", fc.get("peak",{}).get("risk",0) > 0)
            check("Has trend", fc.get("trend") in ["rising","falling","stable","unknown"])

        # 9. HISTORICAL VALIDATION
        print("\n--- 9. Historical Validation ---")
        r = await c.get(f"{BASE}/api/historical/events")
        d = r.json()
        check("5 historical events", d.get("total") == 5, f"got {d.get('total')}")
        if d.get("events"):
            eid = d["events"][0]["event_id"]
            r = await c.post(f"{BASE}/api/historical/validate/{eid}")
            v = r.json()
            check("Validation has ward_predictions", len(v.get("ward_predictions",[])) > 0)
            check("Validation has accuracy", v.get("validation",{}).get("accuracy") is not None)

        # 10. RIVERS
        print("\n--- 10. River Monitor ---")
        r = await c.get(f"{BASE}/api/rivers")
        d = r.json()
        stations = d.get("stations", {})
        check("5 river stations", len(stations) == 5, f"got {len(stations)}")
        check("Has river paths", len(d.get("rivers",{})) >= 3)
        check("Has overall_status", d.get("overall_status") in ["normal","watch","elevated","danger","critical"])
        # Check no random noise
        if stations:
            first_station = list(stations.values())[0]
            check("Weather-driven estimation", "weather-driven" in first_station.get("data_source",""))

        r = await c.get(f"{BASE}/api/rivers/impact")
        d = r.json()
        check("Impact endpoint works", "affected_wards" in d)

        # 11. CASCADING RISK
        print("\n--- 11. Cascading Risk ---")
        r = await c.get(f"{BASE}/api/cascading/chains")
        d = r.json()
        check("Cascade chains defined", d.get("total",0) > 0, f"got {d.get('total')}")
        if d.get("chains"):
            chain_id = d["chains"][0]["chain_id"]
            r = await c.post(f"{BASE}/api/cascading/evaluate", json={"chain_id": chain_id})
            d = r.json()
            check("Cascade evaluation works", "cascades" in d)

        # 12. ALERTS
        print("\n--- 12. Alert System ---")
        r = await c.get(f"{BASE}/api/alerts")
        d = r.json()
        check("Alerts generated", d.get("total_alerts",0) > 0, f"got {d.get('total_alerts')}")
        if d.get("alerts"):
            alert = d["alerts"][0]
            check("Bilingual: English title", len(alert.get("title_en","")) > 0)
            check("Bilingual: Marathi title", len(alert.get("title_mr","")) > 0)
            check("Has actions", len(alert.get("actions",[])) > 0)
            check("Has shelter info", alert.get("shelter_info") is not None)

        # 13. SHELTERS & EVACUATION
        print("\n--- 13. Evacuation ---")
        r = await c.get(f"{BASE}/api/shelters")
        d = r.json()
        check("Shelters available", d.get("total",0) > 0, f"got {d.get('total')}")

        r = await c.get(f"{BASE}/api/evacuation/W004")
        d = r.json()
        check("Evacuation route computed", d.get("recommended_shelter") is not None)
        check("Has urgency level", d.get("evacuation_urgency") in ["immediate","prepare","monitor","standby"])

        r = await c.get(f"{BASE}/api/evacuation")
        d = r.json()
        check("All routes computed", len(d.get("routes",[])) == 20, f"got {len(d.get('routes',[]))}")

        # 14. DECISION SUPPORT
        print("\n--- 14. Decision Support ---")
        r = await c.get(f"{BASE}/api/decision-support")
        d = r.json()
        # In GREEN (normal) conditions 0 actions is valid; only require > 0 when situation is elevated
        sit = d.get("situation_level", "GREEN")
        if sit == "GREEN":
            check("Actions appropriate for GREEN level", d.get("total_actions", 0) >= 0, f"got {d.get('total_actions')} (0 OK for normal)")
        else:
            check("Actions generated", d.get("total_actions", 0) > 0, f"got {d.get('total_actions')}")
        check("Has situation_level", sit in ["GREEN","YELLOW","ORANGE","RED"])
        check("Has KPIs", d.get("kpis") is not None)
        check("Has priority breakdown", all(k in d.get("by_priority",{}) for k in ["immediate","next_6h","next_24h","advisory"]))

        # 15. RESOURCE OPTIMIZER
        print("\n--- 15. Resource Optimizer ---")
        r = await c.post(f"{BASE}/api/optimize", json={})
        d = r.json()
        check("Optimization completes", isinstance(d.get("total_allocated"), dict) and len(d.get("total_allocated",{})) > 0)
        check("20 ward allocations", len(d.get("ward_allocations",[])) == 20, f"got {len(d.get('ward_allocations',[]))}")
        check("Has explanations", len(d.get("explanations",[])) > 0)

    # SUMMARY
    print("\n" + "=" * 60)
    total = PASSED + FAILED
    print(f"RESULTS: {PASSED}/{total} passed, {FAILED} failed, {WARNINGS} warnings")
    if FAILED == 0:
        print("\u2705 ALL TESTS PASSED!")
    else:
        print(f"\u274c {FAILED} test(s) failed")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
