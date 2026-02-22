"""Comprehensive feature testing script for PRAKALP"""
import asyncio
import json
import httpx
import sys

BASE = "http://localhost:8000"
ISSUES = []

def ok(msg):
    print(f"  ✅ {msg}")

def fail(msg):
    print(f"  ❌ {msg}")
    ISSUES.append(msg)

def warn(msg):
    print(f"  ⚠️  {msg}")

async def main():
    async with httpx.AsyncClient(timeout=30) as c:

        # ========== 1. HEALTH ==========
        print("\n═══ 1. HEALTH ═══")
        r = await c.get(f"{BASE}/health")
        d = r.json()
        if d.get("status") == "healthy":
            ok(f"Server healthy, v{d['version']}")
        else:
            fail(f"Server unhealthy: {d}")
        if d.get("data", {}).get("wards_loaded") == 20:
            ok("20 wards loaded")
        else:
            fail(f"Expected 20 wards, got {d.get('data', {}).get('wards_loaded')}")
        ml = d.get("services", {}).get("ml_model")
        if ml == "loaded":
            ok("ML model loaded")
        else:
            fail(f"ML model status: {ml}")

        # ========== 2. WARDS ==========
        print("\n═══ 2. WARDS ═══")
        r = await c.get(f"{BASE}/api/wards")
        d = r.json()
        wards = d.get("wards", [])
        if len(wards) == 20:
            ok(f"20 wards returned")
        else:
            fail(f"Expected 20 wards, got {len(wards)}")
        
        # Check ward data completeness
        w3 = next((w for w in wards if w["ward_id"] == "W003"), None)
        if w3:
            required_fields = ["name", "population", "population_density", "elevation_m", 
                             "drainage_index", "elderly_ratio", "centroid_lat", "centroid_lon"]
            missing = [f for f in required_fields if w3.get(f) is None]
            if not missing:
                ok(f"Ward W003 (Shivajinagar) has all required fields")
            else:
                fail(f"W003 missing fields: {missing}")
            
            # Sanity check Pune coordinates
            lat, lon = w3.get("centroid_lat", 0), w3.get("centroid_lon", 0)
            if 18.4 < lat < 18.65 and 73.73 < lon < 73.97:
                ok(f"W003 coordinates valid ({lat}, {lon})")
            else:
                fail(f"W003 coordinates out of Pune range: ({lat}, {lon})")
        
        # ========== 3. RISK SCORES ==========
        print("\n═══ 3. RISK SCORES ═══")
        r = await c.get(f"{BASE}/api/risk")
        d = r.json()
        risk_data = d.get("risk_data", [])
        if len(risk_data) == 20:
            ok("20 risk scores returned")
        else:
            fail(f"Expected 20 risk scores, got {len(risk_data)}")
        
        scores = [w["top_risk_score"] for w in risk_data]
        min_s, max_s, avg_s = min(scores), max(scores), sum(scores)/len(scores)
        spread = max_s - min_s
        
        # Check: scores should be 0-100
        if all(0 <= s <= 100 for s in scores):
            ok(f"All scores in valid range [0-100]")
        else:
            fail(f"Some scores out of range")
        
        # Check: reasonable spread (not all identical)
        if spread > 10:
            ok(f"Good score spread: {min_s:.1f} - {max_s:.1f} (range={spread:.1f})")
        else:
            fail(f"Poor score spread: {min_s:.1f} - {max_s:.1f} (range={spread:.1f}) — wards too similar")
        
        # Check: not all same category
        cats = {}
        for w in risk_data:
            s = w["top_risk_score"]
            cat = "critical" if s >= 80 else "high" if s >= 60 else "moderate" if s >= 30 else "low"
            cats[cat] = cats.get(cat, 0) + 1
        
        if len(cats) >= 2:
            ok(f"Multiple risk categories: {cats}")
        else:
            warn(f"Only one risk category: {cats} — expected some diversity")

        # Check: flood should be low on dry day, heat moderate
        avg_flood = sum(w["flood"]["event"] for w in risk_data) / len(risk_data)
        avg_heat = sum(w["heat"]["event"] for w in risk_data) / len(risk_data)
        
        if avg_flood < 25:
            ok(f"Avg flood event risk={avg_flood:.1f} (low, correct for dry day)")
        else:
            fail(f"Avg flood event risk={avg_flood:.1f} — too high for a dry day")
        
        # Each ward should have flood/heat sub-objects
        sample = risk_data[0]
        if "flood" in sample and "heat" in sample:
            fl = sample["flood"]
            if all(k in fl for k in ["baseline", "event", "delta", "delta_pct"]):
                ok("Flood sub-object has baseline/event/delta/delta_pct")
            else:
                fail(f"Flood sub-object missing fields: {fl.keys()}")
        else:
            fail("Risk data missing flood/heat sub-objects")

        # ========== 4. RISK SUMMARY ==========
        print("\n═══ 4. RISK SUMMARY ═══")
        r = await c.get(f"{BASE}/api/risk/summary")
        d = r.json()
        
        if d.get("total_wards") == 20:
            ok("total_wards = 20")
        else:
            fail(f"total_wards = {d.get('total_wards')}")
        
        pop = d.get("total_population", 0)
        if 3_000_000 < pop < 6_000_000:
            ok(f"total_population = {pop:,} (reasonable for Pune)")
        else:
            fail(f"total_population = {pop:,} — unrealistic for Pune")
        
        status = d.get("overall_status")
        if status in ["normal", "elevated", "high", "critical"]:
            ok(f"overall_status = '{status}'")
        else:
            fail(f"overall_status = '{status}' — invalid")
        
        dist = d.get("risk_distribution", {})
        total_dist = sum(dist.values())
        if total_dist == 20:
            ok(f"risk_distribution sums to 20: {dict(dist)}")
        else:
            fail(f"risk_distribution sums to {total_dist}: {dict(dist)}")
        
        # Check alerts section
        alerts = d.get("alerts", {})
        surge_wards = alerts.get("surge_wards", [])
        critical_ws = alerts.get("critical_wards", [])
        ok(f"Surge alerts: {len(surge_wards)} wards, Critical alerts: {len(critical_ws)} wards")
        
        # ========== 5. RISK EXPLANATION ==========
        print("\n═══ 5. RISK EXPLANATION ═══")
        
        # Test for a ward
        for test_ward in ["W003", "W019"]:
            r = await c.get(f"{BASE}/api/risk/explain/{test_ward}")
            if r.status_code != 200:
                fail(f"Explain {test_ward}: HTTP {r.status_code}")
                continue
            d = r.json()
            
            name = d.get("ward_name", "?")
            bl = d.get("baseline_risk")
            ev = d.get("event_risk")
            delta = d.get("delta")
            delta_pct = d.get("delta_pct")
            surge = d.get("surge_level")
            narrative = d.get("narrative")
            drivers = d.get("top_drivers_event", [])
            recs = d.get("recommendations", [])
            conf = d.get("confidence")
            
            if bl is not None and ev is not None:
                ok(f"{test_ward} ({name}): baseline={bl:.1f}, event={ev:.1f}, delta={delta:+.1f} ({delta_pct:+.1f}%)")
            else:
                fail(f"{test_ward} missing baseline/event risk")
            
            if surge in ["stable", "elevated", "surge", "critical", "decreasing"]:
                ok(f"  surge_level='{surge}'")
            else:
                fail(f"  surge_level='{surge}' — invalid")
            
            if narrative and len(narrative) > 20:
                ok(f"  narrative present ({len(narrative)} chars)")
            else:
                fail(f"  narrative missing or too short: '{narrative}'")
            
            if len(drivers) > 0:
                ok(f"  {len(drivers)} top_drivers_event")
            else:
                fail(f"  No top_drivers_event")
            
            if len(recs) > 0:
                ok(f"  {len(recs)} recommendations")
            else:
                fail(f"  No recommendations")
            
            if conf is not None and 0 <= conf <= 1:
                ok(f"  confidence={conf:.2f}")
            else:
                fail(f"  confidence invalid: {conf}")

        # ========== 6. WEATHER ==========
        print("\n═══ 6. WEATHER ═══")
        r = await c.get(f"{BASE}/api/weather/W001")
        if r.status_code == 200:
            d = r.json()
            current = d.get("current", {})
            temp = current.get("temperature_c")
            rain = current.get("rainfall_mm")
            humidity = current.get("humidity_pct")
            
            if temp is not None:
                if 5 < temp < 50:
                    ok(f"W001 temp={temp}°C (reasonable)")
                else:
                    fail(f"W001 temp={temp}°C — unrealistic")
            else:
                fail("W001 temperature_c missing")
            
            if rain is not None:
                ok(f"W001 rainfall={rain}mm")
            else:
                fail("W001 rainfall_mm missing")
            
            if humidity is not None and 0 <= humidity <= 100:
                ok(f"W001 humidity={humidity}%")
            else:
                fail(f"W001 humidity invalid: {humidity}")
            
            forecast = d.get("forecast", {})
            if forecast:
                ok(f"Forecast data present: {list(forecast.keys())[:5]}")
            else:
                warn("No forecast data")
        else:
            fail(f"Weather endpoint HTTP {r.status_code}")

        # ========== 7. 48h FORECAST ==========
        print("\n═══ 7. 48h FORECAST ═══")
        r = await c.get(f"{BASE}/api/forecast/48h")
        if r.status_code == 200:
            d = r.json()
            forecasts = d.get("forecasts", [])
            if len(forecasts) == 20:
                ok(f"20 ward forecasts")
            else:
                fail(f"Expected 20 forecasts, got {len(forecasts)}")
            
            if forecasts:
                f0 = forecasts[0]
                timeline = f0.get("timeline", [])
                if len(timeline) > 0:
                    ok(f"First ward has {len(timeline)} timeline entries")
                    # Check timeline has required fields
                    t0 = timeline[0]
                    required = ["hour", "risk_score"]
                    missing = [k for k in required if k not in t0]
                    if not missing:
                        ok(f"Timeline entry has required fields")
                    else:
                        fail(f"Timeline entry missing: {missing}")
                else:
                    fail("Empty timeline")
                
                peak = f0.get("peak", {})
                if peak and "risk_score" in peak:
                    ok(f"Peak data: score={peak['risk_score']}")
                else:
                    fail(f"Peak data missing or incomplete")
                
                trend = f0.get("trend")
                if trend in ["increasing", "decreasing", "stable", "fluctuating"]:
                    ok(f"trend='{trend}'")
                else:
                    fail(f"trend='{trend}' — invalid")
        else:
            fail(f"48h forecast HTTP {r.status_code}")

        # ========== 8. SCENARIO SIMULATION ==========
        print("\n═══ 8. SCENARIO SIMULATION ═══")
        
        # Test cloudburst scenario
        scenario = {
            "rainfall_mm": 120,
            "duration_hours": 6,
            "affected_wards": ["W003", "W004", "W005"]
        }
        r = await c.post(f"{BASE}/api/scenario", json=scenario)
        if r.status_code == 200:
            d = r.json()
            ok(f"Scenario simulation returned")
            
            agg = d.get("aggregate_impact", {})
            if agg:
                ok(f"aggregate_impact: avg_risk={agg.get('average_risk_score', '?')}, pop_at_risk={agg.get('population_at_risk', '?')}")
            else:
                fail("No aggregate_impact")
            
            ward_results = d.get("ward_results", [])
            if len(ward_results) > 0:
                wr = ward_results[0]
                before = wr.get("risk_before", 0)
                after = wr.get("risk_after", 0)
                if after > before:
                    ok(f"Risk increases under scenario: {before:.1f} → {after:.1f} for {wr.get('ward_id')}")
                else:
                    warn(f"Risk didn't increase: {before:.1f} → {after:.1f} — cloudburst should increase flood risk")
            else:
                fail("No ward_results in scenario")
        else:
            fail(f"Scenario simulation HTTP {r.status_code}")
        
        # Test custom scenario (frontend format)
        custom = {"scenario_type": "cloudburst", "intensity": "extreme"}
        r = await c.post(f"{BASE}/api/scenario", json=custom)
        if r.status_code == 200:
            ok("Custom scenario (frontend format) works")
        else:
            fail(f"Custom scenario HTTP {r.status_code}")

        # ========== 9. HISTORICAL VALIDATION ==========
        print("\n═══ 9. HISTORICAL VALIDATION ═══")
        r = await c.get(f"{BASE}/api/historical")
        if r.status_code == 200:
            d = r.json()
            events = d if isinstance(d, list) else d.get("events", [])
            if len(events) >= 3:
                ok(f"{len(events)} historical events")
                for ev in events[:3]:
                    eid = ev.get("event_id", "?")
                    etype = ev.get("event_type", "?")
                    edate = ev.get("date", "?")
                    print(f"      {eid}: {etype} on {edate}")
            else:
                fail(f"Only {len(events)} historical events — expected >= 3")
        else:
            fail(f"Historical events HTTP {r.status_code}")
        
        # Validate a specific event
        r = await c.post(f"{BASE}/api/historical/validate/pune_2019_sep")
        if r.status_code == 200:
            d = r.json()
            validation = d.get("validation", {})
            accuracy = validation.get("accuracy")
            if accuracy is not None:
                if accuracy > 0.5:
                    ok(f"Validation accuracy={accuracy:.2f} (>{0.5})")
                else:
                    warn(f"Validation accuracy={accuracy:.2f} — low")
            else:
                fail("No accuracy in validation")
            
            wp = d.get("ward_predictions", [])
            if len(wp) > 0:
                ok(f"{len(wp)} ward predictions")
            else:
                fail("No ward predictions")
        else:
            fail(f"Historical validation HTTP {r.status_code}")

        # ========== 10. RIVER MONITOR ==========
        print("\n═══ 10. RIVER MONITOR ═══")
        r = await c.get(f"{BASE}/api/rivers")
        if r.status_code == 200:
            d = r.json()
            stations = d.get("stations", d.get("rivers", []))
            if isinstance(d, list):
                stations = d
            
            if len(stations) >= 3:
                ok(f"{len(stations)} river stations")
            else:
                fail(f"Only {len(stations)} river stations")
            
            if stations:
                s0 = stations[0] if isinstance(stations, list) else stations
                name = s0.get("name", s0.get("station_name", "?"))
                level = s0.get("current_level_m", s0.get("level", "?"))
                status = s0.get("status", "?")
                ds = s0.get("data_source", "?")
                ok(f"Station: {name}, level={level}m, status={status}")
                if "weather" in str(ds).lower() or "estimation" in str(ds).lower():
                    ok(f"data_source='{ds}' (weather-driven, not random)")
                elif "random" in str(ds).lower() or "mock" in str(ds).lower():
                    fail(f"data_source='{ds}' — should not be random/mock!")
                else:
                    ok(f"data_source='{ds}'")
            
            # Check river paths
            paths = d.get("river_paths", [])
            if paths:
                ok(f"{len(paths)} river paths with coordinates")
            else:
                warn("No river_paths in response")
            
            overall = d.get("overall_status")
            if overall:
                ok(f"overall_status='{overall}'")
            else:
                warn("No overall_status")
        else:
            fail(f"River monitor HTTP {r.status_code}")
        
        # River impact
        r = await c.get(f"{BASE}/api/rivers/impact")
        if r.status_code == 200:
            ok("River impact endpoint works")
        else:
            fail(f"River impact HTTP {r.status_code}")

        # ========== 11. CASCADING RISK ==========
        print("\n═══ 11. CASCADING RISK ═══")
        r = await c.get(f"{BASE}/api/cascading/chains")
        if r.status_code == 200:
            d = r.json()
            chains = d if isinstance(d, list) else d.get("chains", [])
            if len(chains) > 0:
                ok(f"{len(chains)} cascade chains defined")
                c0 = chains[0]
                print(f"      Chain: {c0.get('name', c0.get('chain_id', '?'))}")
            else:
                fail("No cascade chains")
        else:
            fail(f"Cascading chains HTTP {r.status_code}")
        
        r = await c.get(f"{BASE}/api/cascading/evaluate/W003")
        if r.status_code == 200:
            d = r.json()
            ok(f"Cascade evaluation for W003")
            if "final_risk" in d or "risk_increase" in d or "chains" in d:
                ok(f"Has risk data in cascade evaluation")
            else:
                warn(f"Cascade response keys: {list(d.keys())[:8]}")
        else:
            fail(f"Cascade evaluate HTTP {r.status_code}")

        # ========== 12. ALERTS (BILINGUAL) ==========
        print("\n═══ 12. ALERTS (BILINGUAL) ═══")
        r = await c.get(f"{BASE}/api/alerts")
        if r.status_code == 200:
            d = r.json()
            alerts_list = d if isinstance(d, list) else d.get("alerts", [])
            if len(alerts_list) > 0:
                ok(f"{len(alerts_list)} alerts generated")
                a0 = alerts_list[0]
                
                # Check English title
                title_en = a0.get("title_en", a0.get("title", ""))
                if title_en:
                    ok(f"English title: '{title_en[:60]}...'")
                else:
                    fail("No English title")
                
                # Check Marathi title
                title_mr = a0.get("title_mr", "")
                if title_mr:
                    ok(f"Marathi title: '{title_mr[:60]}...'")
                else:
                    fail("No Marathi title — bilingual requirement")
                
                # Check actions
                actions = a0.get("actions", [])
                if len(actions) > 0:
                    ok(f"{len(actions)} actions: {actions[:2]}")
                else:
                    fail("No actions in alert")
                
                # Check shelter info
                shelters = a0.get("shelters", a0.get("nearest_shelters", []))
                if shelters:
                    ok(f"Shelter info present ({len(shelters)} shelters)")
                else:
                    warn("No shelter info in alert")
                
                # Check severity
                severity = a0.get("severity", a0.get("level", "?"))
                if severity in ["info", "warning", "severe", "critical", "advisory", "watch"]:
                    ok(f"severity='{severity}'")
                else:
                    warn(f"severity='{severity}' — check if valid")
            else:
                warn("0 alerts — may be correct for normal conditions")
        else:
            fail(f"Alerts HTTP {r.status_code}")

        # ========== 13. EVACUATION & SHELTERS ==========
        print("\n═══ 13. EVACUATION & SHELTERS ═══")
        r = await c.get(f"{BASE}/api/evacuation/shelters")
        if r.status_code == 200:
            d = r.json()
            shelters = d if isinstance(d, list) else d.get("shelters", [])
            if len(shelters) > 0:
                ok(f"{len(shelters)} shelters available")
                s0 = shelters[0]
                name = s0.get("name", "?")
                cap = s0.get("capacity", "?")
                lat = s0.get("lat", s0.get("latitude", "?"))
                lon = s0.get("lon", s0.get("longitude", "?"))
                ok(f"  Sample: {name}, capacity={cap}, ({lat}, {lon})")
                
                # Sanity: are coordinates in Pune?
                if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
                    if 18.3 < lat < 18.7 and 73.7 < lon < 74.0:
                        ok(f"  Shelter coordinates in Pune range")
                    else:
                        fail(f"  Shelter coordinates ({lat}, {lon}) — outside Pune!")
            else:
                fail("No shelters")
        else:
            fail(f"Shelters HTTP {r.status_code}")
        
        # Evacuation route
        r = await c.get(f"{BASE}/api/evacuation/route/W003")
        if r.status_code == 200:
            d = r.json()
            ok(f"Evacuation route for W003")
            urgency = d.get("urgency_level", d.get("urgency", "?"))
            ok(f"  urgency='{urgency}'")
            
            route = d.get("route", d.get("routes", []))
            if route:
                ok(f"  Route data present")
            else:
                warn("  No route data")
            
            shelters = d.get("shelters", d.get("nearest_shelters", []))
            if shelters:
                ok(f"  {len(shelters)} nearby shelters")
            else:
                warn("  No shelter recommendations in route")
        else:
            fail(f"Evacuation route HTTP {r.status_code}")

        # ========== 14. DECISION SUPPORT ==========
        print("\n═══ 14. DECISION SUPPORT ═══")
        r = await c.get(f"{BASE}/api/decision-support")
        if r.status_code == 200:
            d = r.json()
            sit = d.get("situation_level", "?")
            total_actions = d.get("total_actions", 0)
            kpis = d.get("kpis", {})
            by_prio = d.get("by_priority", {})
            actions = d.get("actions", [])
            
            if sit in ["GREEN", "YELLOW", "ORANGE", "RED"]:
                ok(f"situation_level='{sit}'")
            else:
                fail(f"situation_level='{sit}' — invalid")
            
            if sit == "GREEN" and total_actions == 0:
                ok(f"0 actions for GREEN level (correct — no emergency)")
            elif total_actions > 0:
                ok(f"{total_actions} actions generated")
            else:
                warn(f"situation_level={sit} but 0 actions")
            
            if kpis:
                ok(f"KPIs: {json.dumps(kpis, default=str)[:100]}")
            else:
                fail("No KPIs")
            
            expected_prios = ["immediate", "next_6h", "next_24h", "advisory"]
            if all(k in by_prio for k in expected_prios):
                ok(f"Priority breakdown: {dict(by_prio)}")
            else:
                fail(f"Missing priority categories: {by_prio}")
        else:
            fail(f"Decision support HTTP {r.status_code}")

        # ========== 15. RESOURCE OPTIMIZER ==========
        print("\n═══ 15. RESOURCE OPTIMIZER ═══")
        r = await c.post(f"{BASE}/api/optimize", json={})
        if r.status_code == 200:
            d = r.json()
            allocs = d.get("allocations", [])
            if len(allocs) == 20:
                ok(f"20 ward allocations")
            elif len(allocs) > 0:
                ok(f"{len(allocs)} ward allocations")
            else:
                fail("No allocations returned")
            
            if allocs:
                a0 = allocs[0]
                wid = a0.get("ward_id", "?")
                res = a0.get("resources", a0.get("allocated", {}))
                ok(f"  Sample: {wid} → {json.dumps(res, default=str)[:120]}")
            
            explanations = d.get("explanations", [])
            if explanations:
                ok(f"{len(explanations)} allocation explanations")
            else:
                warn("No allocation explanations")
        else:
            fail(f"Resource optimizer HTTP {r.status_code}")

        # ========== 16. CALCULATE RISKS (POST) ==========
        print("\n═══ 16. CALCULATE RISKS (trigger) ═══")
        r = await c.post(f"{BASE}/api/calculate-risks")
        if r.status_code == 200:
            d = r.json()
            computed = d.get("computed", d.get("wards_computed", 0))
            ok(f"Risk recalculation triggered: {json.dumps(d, default=str)[:150]}")
        else:
            fail(f"Calculate risks HTTP {r.status_code}")

        # ========== SUMMARY ==========
        print("\n" + "=" * 60)
        if ISSUES:
            print(f"FOUND {len(ISSUES)} ISSUE(S):")
            for i, issue in enumerate(ISSUES, 1):
                print(f"  {i}. {issue}")
        else:
            print("ALL FEATURES PASSED! ✅")
        print("=" * 60)

    return ISSUES

issues = asyncio.run(main())
sys.exit(1 if issues else 0)
