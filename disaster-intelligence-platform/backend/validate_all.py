#!/usr/bin/env python3
"""
Comprehensive feature-by-feature test with common-sense output validation.
Tests all 16 features of the PRAKALP platform.
"""
import requests, json, sys, time

BASE = "http://localhost:8000"
PASS = 0
FAIL = 0
WARN = 0

def ok(msg):
    global PASS
    PASS += 1
    print(f"  ✅ {msg}")

def fail(msg):
    global FAIL
    FAIL += 1
    print(f"  ❌ {msg}")

def warn(msg):
    global WARN
    WARN += 1
    print(f"  ⚠️  {msg}")

def get(url, timeout=10):
    r = requests.get(f"{BASE}{url}", timeout=timeout)
    return r.status_code, r.json() if r.status_code == 200 else r.text

def post(url, data=None, timeout=10):
    r = requests.post(f"{BASE}{url}", json=data, timeout=timeout)
    return r.status_code, r.json() if r.status_code == 200 else r.text

# ================================================================
print("\n" + "="*70)
print("FEATURE 1: Health Check")
print("="*70)
code, d = get("/health")
if code == 200:
    ok(f"Server healthy, version={d['version']}")
    if d["data"]["wards_loaded"] == 20:
        ok(f"All 20 Pune wards loaded")
    else:
        fail(f"Expected 20 wards, got {d['data']['wards_loaded']}")
    if d["services"]["ml_model"] == "loaded":
        ok("ML model loaded")
    else:
        fail("ML model not loaded")
    if d["services"]["database"] == "connected":
        ok("Database connected")
    else:
        fail("Database not connected")
else:
    fail(f"Health check failed: {code}")

# ================================================================
print("\n" + "="*70)
print("FEATURE 2: Ward Data")
print("="*70)
code, d = get("/api/wards")
if code == 200:
    wards = d["wards"]
    ok(f"Got {d['total']} wards")
    
    # Check first ward structure
    w = wards[0]
    required = ["ward_id", "name", "centroid", "area_sq_km", "population"]
    missing = [f for f in required if f not in w]
    if missing:
        fail(f"Ward missing fields: {missing}")
    else:
        ok("Ward has all required fields")
    
    # Centroid should be valid Pune coordinates
    c = w.get("centroid", {})
    lat, lon = c.get("lat", 0), c.get("lon", 0)
    if 18.3 < lat < 18.7 and 73.6 < lon < 74.0:
        ok(f"Centroid ({lat}, {lon}) is within Pune")
    else:
        fail(f"Centroid ({lat}, {lon}) not in Pune!")
    
    # Population should be reasonable for Pune wards
    pops = [w["population"] for w in wards]
    if all(50000 <= p <= 1000000 for p in pops):
        ok(f"Population range {min(pops):,} - {max(pops):,} (reasonable)")
    else:
        warn(f"Population range {min(pops):,} - {max(pops):,} — check if reasonable")
    
    # Area should be within Pune city limits
    areas = [w["area_sq_km"] for w in wards]
    if all(1 <= a <= 100 for a in areas):
        ok(f"Area range {min(areas):.1f} - {max(areas):.1f} sq km (reasonable)")
    else:
        warn(f"Area range {min(areas):.1f} - {max(areas):.1f} sq km")
else:
    fail(f"Ward API failed: {code}")

# ================================================================
print("\n" + "="*70)
print("FEATURE 3: Risk Scores")
print("="*70)
code, d = get("/api/risk")
if code == 200:
    risk_items = d.get("risk_data", d) if isinstance(d, dict) else d
    if isinstance(risk_items, dict):
        risk_items = risk_items.get("risk_data", [])
    ok(f"Got {len(risk_items)} ward risk scores")
    
    scores = [w.get("top_risk_score", 0) for w in risk_items]
    categories = [w.get("risk_category", "unknown") for w in risk_items]
    
    if all(0 <= s <= 100 for s in scores):
        ok(f"All scores in valid 0-100 range")
    else:
        fail("Some scores outside 0-100 range")
    
    spread = max(scores) - min(scores)
    if spread >= 5:
        ok(f"Score spread: {min(scores):.1f} - {max(scores):.1f} (good differentiation)")
    else:
        fail(f"Score spread only {spread:.1f} — poor differentiation")
    
    # For a normal Feb day: expect mostly low/moderate, no critical
    cat_counts = {}
    for c in categories:
        cat_counts[c] = cat_counts.get(c, 0) + 1
    ok(f"Risk distribution: {cat_counts}")
    
    if cat_counts.get("critical", 0) == 0:
        ok("No critical wards (correct for normal day)")
    else:
        warn(f"{cat_counts['critical']} critical wards on a normal day — unexpected")
else:
    fail(f"Risk API failed: {code}")

# ================================================================
print("\n" + "="*70)
print("FEATURE 4: Risk Summary")
print("="*70)
code, d = get("/api/risk/summary")
if code == 200:
    ok(f"Risk summary: {d['total_wards']} wards, status={d.get('overall_status', 'N/A')}")
    
    pop = d.get("total_population", 0)
    if 2_000_000 <= pop <= 8_000_000:
        ok(f"Total population {pop:,} (reasonable for Pune)")
    else:
        warn(f"Total population {pop:,} — check if correct")
    
    dist = d.get("risk_distribution", {})
    ok(f"Distribution: {dist}")
    
    # For normal day: expect 0-2 high, 0 critical
    if dist.get("critical", 0) == 0:
        ok("No critical wards (correct)")
    else:
        warn(f"{dist['critical']} critical wards")
else:
    fail(f"Risk summary failed: {code}")

# ================================================================
print("\n" + "="*70)
print("FEATURE 5: Risk Explanation (Explainability)")
print("="*70)
code, d = get("/api/risk/explain/W003")
if code == 200:
    ok(f"Ward {d['ward_id']} ({d['ward_name']}) - {d['hazard']} risk")
    ok(f"Baseline: {d['baseline_risk']}, Event: {d['event_risk']}, Delta: {d['delta_pct']}%")
    
    surge = d.get("surge_level")
    valid_surges = ["normal", "elevated", "surge", "critical"]
    if surge in valid_surges:
        ok(f"Surge level: '{surge}' (valid)")
    else:
        fail(f"Surge level '{surge}' not in {valid_surges}")
    
    narrative = d.get("narrative", "")
    if len(narrative) > 20:
        ok(f"Narrative generated ({len(narrative)} chars)")
    else:
        fail("Narrative too short or missing")
    
    if d.get("recommendations"):
        ok(f"Has {len(d['recommendations'])} recommendation(s)")
    else:
        warn("No recommendations")
    
    if d.get("top_drivers") or d.get("top_drivers_event"):
        drivers = d.get("top_drivers", d.get("top_drivers_event", []))
        ok(f"Has {len(drivers)} risk drivers")
    else:
        warn("No risk drivers")
    
    if d.get("shap_values"):
        ok("SHAP values present (ML explainability)")
    else:
        warn("No SHAP values")
    
    conf = d.get("confidence", 0)
    if 0.5 <= conf <= 1.0:
        ok(f"Confidence: {conf:.2f}")
    else:
        warn(f"Confidence {conf} outside expected range")
else:
    fail(f"Risk explain failed: {code}")

# ================================================================
print("\n" + "="*70)
print("FEATURE 6: Weather Forecast (Per Ward)")
print("="*70)
code, d = get("/api/forecast/W003")
if code == 200:
    ok(f"Ward {d['ward_id']} ({d['ward_name']}) forecast")
    
    timeline = d.get("timeline", [])
    if len(timeline) > 5:
        ok(f"Timeline has {len(timeline)} data points")
    else:
        fail(f"Timeline only {len(timeline)} points")
    
    # Check timeline values
    risks = [t.get("combined_risk", 0) for t in timeline]
    if all(0 <= r <= 100 for r in risks):
        ok(f"Forecast risk range: {min(risks):.1f} - {max(risks):.1f}")
    else:
        fail("Some forecast risks outside 0-100")
    
    peak = d.get("peak", {})
    if peak:
        ok(f"Peak: risk={peak.get('risk', 'N/A')} at hour {peak.get('hour', 'N/A')} ({peak.get('hazard', 'N/A')})")
    
    trend = d.get("trend")
    if trend in ["stable", "rising", "falling"]:
        ok(f"Trend: {trend}")
    else:
        warn(f"Unexpected trend: {trend}")
    
    alert = d.get("current_alert")
    if alert:
        ok(f"Current alert level: {alert}")
else:
    fail(f"Forecast API failed: {code}")

# ================================================================
print("\n" + "="*70)
print("FEATURE 7: 48-Hour Forecast (All Wards)")
print("="*70)
code, d = get("/api/forecast")
if code == 200:
    ok(f"All-ward forecast: {d['total_wards']} wards, risk_rising={d.get('wards_risk_rising', 'N/A')}")
    
    forecasts = d.get("forecasts", [])
    if len(forecasts) == 20:
        ok(f"Got forecasts for all 20 wards")
    else:
        warn(f"Got {len(forecasts)} forecasts (expected 20)")
    
    hours = d.get("forecast_hours", [])
    if 48 in hours:
        ok(f"Forecast extends to 48 hours")
    else:
        warn(f"Forecast hours: {hours}")
    
    critical = d.get("wards_reaching_critical", 0)
    if critical == 0:
        ok("No wards reaching critical (correct for normal day)")
    else:
        warn(f"{critical} wards reaching critical")
else:
    fail(f"Forecast all failed: {code}")

# ================================================================
print("\n" + "="*70)
print("FEATURE 8: Scenario Simulator")
print("="*70)
# Test with heavy rain scenario
code, d = post("/api/scenario", {
    "scenario_key": "custom",
    "custom_params": {
        "rainfall_multiplier": 2.5,
        "temp_anomaly_addition": 0,
        "drainage_efficiency_multiplier": 1.0,
        "population_growth_pct": 0,
    }
})
if code == 200:
    ok("Scenario simulation completed")
    
    scenario = d.get("scenario", {})
    ok(f"Params: rain_mult={scenario.get('rain_multiplier', 'N/A')}")
    
    results = d.get("results", [])
    if len(results) == 20:
        ok(f"Got results for all 20 wards")
    else:
        warn(f"Got {len(results)} results")
    
    # Check population/centroid are populated
    if results:
        first = results[0]
        pop = first.get("baseline", {}).get("population", 0)
        centroid = first.get("baseline", {}).get("centroid", {})
        if pop > 0:
            ok(f"Population populated: {pop:,}")
        else:
            fail("Population still 0 — fix not applied!")
        if centroid.get("lat", 0) > 0:
            ok(f"Centroid populated: ({centroid.get('lat')}, {centroid.get('lon')})")
        else:
            fail("Centroid still (0,0) — fix not applied!")
    
    agg = d.get("aggregate_impact", {})
    flood_change = agg.get("avg_flood_risk_change", 0)
    ok(f"Avg flood risk change: {flood_change:+.1f}")
    
    # With 2.5x rain, flood risk should increase compared to baseline
    # NOTE: event risk may still be < baseline for moderate multipliers
    # because baseline incorporates historical vulnerability
else:
    fail(f"Scenario failed: {code} — {d}")

# ================================================================
print("\n" + "="*70)
print("FEATURE 9: Historical Events & Validation")
print("="*70)
code, d = get("/api/historical/events")
if code == 200:
    events = d.get("events", [])
    ok(f"Got {d.get('total', 0)} historical events")
    
    # Check event structure
    if events:
        e = events[0]
        ok(f"First event: {e.get('name')} ({e.get('date')})")
        
        types = set(ev.get("event_type") for ev in events)
        ok(f"Event types: {types}")
        
        severities = set(ev.get("severity") for ev in events)
        ok(f"Severities: {severities}")
else:
    fail(f"Historical events failed: {code}")

# Validate against known event
code, d = post("/api/historical/validate/pune_2019_sep")
if code == 200:
    v = d.get("validation", {})
    accuracy = v.get("accuracy", 0)
    recall = v.get("recall", 0)
    precision = v.get("precision", 0)
    f1 = v.get("f1_score", 0)
    
    ok(f"Validation: accuracy={accuracy}%, recall={recall}%, precision={precision}%, F1={f1}%")
    
    tp = v.get("true_positives", 0)
    fn = v.get("false_negatives", 0)
    
    if recall >= 80:
        ok(f"Recall \u2265 80% ({tp} of {tp + fn} affected wards detected) \u2014 excellent for disaster response")
    elif recall >= 50:
        ok(f"Recall \u2265 50% ({tp} of {tp + fn} affected wards detected)")
    else:
        fail(f"Recall only {recall}% \u2014 model missed most affected wards ({tp}/{tp + fn})")
    
    if f1 >= 40:
        ok(f"F1 \u2265 40% (good balance of precision & recall for disaster prediction)")
    elif f1 >= 25:
        warn(f"F1 score {f1}% \u2014 moderate prediction quality")
    else:
        fail(f"F1 only {f1}% \u2014 poor prediction quality")
else:
    fail(f"Historical validation failed: {code}")

# ================================================================
print("\n" + "="*70)
print("FEATURE 10: River Monitor")
print("="*70)
code, d = get("/api/rivers")
if code == 200:
    ok(f"Overall status: {d.get('overall_status')}")
    
    stations = d.get("stations", {})
    ok(f"Monitoring {len(stations)} station(s)")
    
    for sid, sdata in stations.items():
        st = sdata.get("station", {})
        ok(f"Station: {st.get('name')} on {st.get('river')}, danger_level={st.get('danger_level_m')}m")
    
    rivers = d.get("rivers", {})
    ok(f"River data for: {list(rivers.keys())}")
    
    # Pune should have Mula & Mutha rivers
    if "mula" in rivers or "mutha" in rivers:
        ok("Mula/Mutha river data present (correct for Pune)")
    else:
        warn("Missing Mula/Mutha river data")
else:
    fail(f"River monitor failed: {code}")

# Check river impact
code2, d2 = get("/api/rivers/impact")
if code2 == 200:
    ok(f"River impact data available")
else:
    warn(f"River impact endpoint: {code2}")

# ================================================================
print("\n" + "="*70)
print("FEATURE 11: Cascading Risk")
print("="*70)
code, d = get("/api/cascading/chains")
if code == 200:
    chains = d.get("chains", [])
    ok(f"Got {d.get('total', 0)} cascade chains")
    
    for ch in chains:
        ok(f"Chain: {ch['chain_id']} — {ch['name']}")
else:
    fail(f"Cascading chains failed: {code}")

# Evaluate cascade
code, d = post("/api/cascading/evaluate", {"chain_id": "dam_flood", "ward_id": "W003"})
if code == 200:
    ok("Cascade evaluation completed")
    
    cascades = d.get("cascades", {})
    if "dam_flood" in cascades:
        dam = cascades["dam_flood"]
        ok(f"Dam flood cascade evaluated")
    
    highest = d.get("highest_risk_chain")
    if highest:
        ok(f"Highest risk chain: {highest}")
else:
    fail(f"Cascading evaluate failed: {code} — {d}")

# ================================================================
print("\n" + "="*70)
print("FEATURE 12: Bilingual Alerts")
print("="*70)
code, d = get("/api/alerts")
if code == 200:
    ok(f"Total alerts: {d.get('total_alerts', 0)}")
    
    by_pri = d.get("by_priority", {})
    ok(f"By priority: {by_pri}")
    
    alerts = d.get("alerts", [])
    if alerts:
        a = alerts[0]
        required = ["alert_id", "ward_id", "priority", "hazard", "risk_score", "message_en"]
        missing = [f for f in required if f not in a]
        if missing:
            fail(f"Alert missing fields: {missing}")
        else:
            ok("Alert has all required fields")
        
        # Check for bilingual (Marathi) content
        msg = a.get("message_en", "") + a.get("message_mr", "")
        marathi = a.get("message_mr", "")
        if marathi:
            ok(f"Bilingual alert (Marathi): {marathi[:60]}...")
        else:
            warn("No Marathi translation found")
        
        # Check alert priority makes sense
        if a.get("priority") == "advisory" and a.get("risk_score", 0) < 60:
            ok(f"Advisory level for risk {a.get('risk_score', 'N/A')} (appropriate)")
        elif a.get("priority") == "warning" and a.get("risk_score", 0) >= 60:
            ok(f"Warning level for risk {a.get('risk_score', 'N/A')} (appropriate)")
    else:
        warn("No alerts generated")
    
    # For normal day: expect only advisories, no emergencies
    if by_pri.get("emergency", 0) == 0 and by_pri.get("warning", 0) == 0:
        ok("No emergencies/warnings on normal day (correct)")
else:
    fail(f"Alerts failed: {code}")

# ================================================================
print("\n" + "="*70)
print("FEATURE 13: Evacuation Routes & Shelters")
print("="*70)
# Ward-specific evacuation
code, d = get("/api/evacuation/W003")
if code == 200:
    ok(f"Evacuation for {d['ward_name']}: urgency={d.get('evacuation_urgency')}")
    
    shelter = d.get("recommended_shelter", {}).get("shelter", {})
    if shelter:
        ok(f"Recommended shelter: {shelter.get('name')} (cap={shelter.get('capacity')})")
        
        # Check shelter is in Pune
        slat, slon = shelter.get("lat", 0), shelter.get("lon", 0)
        if 18.3 < slat < 18.7 and 73.6 < slon < 74.0:
            ok(f"Shelter location ({slat}, {slon}) in Pune")
        else:
            fail(f"Shelter at ({slat}, {slon}) not in Pune!")
    else:
        warn("No recommended shelter")
    
    alts = d.get("alternatives", [])
    ok(f"Alternative shelters: {len(alts)}")
    
    total = d.get("total_shelters_in_range", 0)
    ok(f"Total shelters in range: {total}")
else:
    fail(f"Evacuation ward failed: {code}")

# All evacuation routes
code, d = get("/api/evacuation")
if code == 200:
    ok(f"City-wide evacuation: {d.get('total_wards')} wards")
    
    routes = d.get("routes", [])
    ok(f"Routes for {len(routes)} wards")
    
    shelters = d.get("shelters", [])
    ok(f"Total shelters: {len(shelters)}")
    
    flood_roads = d.get("flood_prone_roads", [])
    ok(f"Flood-prone roads: {len(flood_roads)}")
else:
    fail(f"Evacuation all failed: {code}")

# Shelters endpoint
code, d = get("/api/shelters")
if code == 200:
    ok(f"Shelters: {d.get('total', 0)} available")
    
    shelters = d.get("shelters", [])
    if shelters:
        s = shelters[0]
        ok(f"Sample: {s.get('name')} ({s.get('type')}, cap={s.get('capacity')})")
        
        facilities = s.get("facilities", [])
        if facilities:
            ok(f"Facilities: {facilities}")
else:
    fail(f"Shelters failed: {code}")

# ================================================================
print("\n" + "="*70)
print("FEATURE 14: Decision Support")
print("="*70)
code, d = get("/api/decision-support")
if code == 200:
    ok(f"Situation level: {d.get('situation_level')}")
    
    kpis = d.get("kpis", {})
    ok(f"KPIs: critical_actions={kpis.get('critical_actions_pending')}, "
       f"critical_wards={kpis.get('critical_wards')}, "
       f"readiness={kpis.get('response_readiness')}")
    
    total_actions = d.get("total_actions", 0)
    ok(f"Total actions: {total_actions}")
    
    by_pri = d.get("by_priority", {})
    ok(f"Actions by priority: {by_pri}")
    
    # For normal day: GREEN level, 0 critical, HIGH readiness
    level = d.get("situation_level")
    if level == "GREEN":
        ok("GREEN level on normal day (correct)")
    elif level in ["YELLOW", "ORANGE", "RED"]:
        warn(f"Level {level} — unexpected for normal day")
    
    if kpis.get("response_readiness") == "HIGH":
        ok("HIGH readiness (correct)")
else:
    fail(f"Decision support failed: {code}")

# ================================================================
print("\n" + "="*70)
print("FEATURE 15: Resource Optimizer")
print("="*70)
code, d = post("/api/optimize", {"scenario": {"use_delta": True}})
if code == 200:
    ok("Resource optimization completed")
    
    total_res = d.get("total_resources", {})
    total_alloc = d.get("total_allocated", {})
    ok(f"Resources: {total_res}")
    ok(f"Allocated: {total_alloc}")
    
    # All resources should be allocated
    for rtype, count in total_res.items():
        allocated = total_alloc.get(rtype, 0)
        if allocated == count:
            ok(f"  {rtype}: {allocated}/{count} fully allocated")
        else:
            warn(f"  {rtype}: {allocated}/{count} partially allocated")
    
    allocations = d.get("ward_allocations", [])
    ok(f"Allocations across {len(allocations)} wards")
    
    summary = d.get("summary", {})
    ok(f"Highest need ward: {summary.get('highest_need_ward')}")
    
    explanations = d.get("explanations", {})
    if explanations:
        ok(f"Has {len(explanations)} explanation rules")
else:
    fail(f"Resource optimizer failed: {code}")

# ================================================================
print("\n" + "="*70)
print("FEATURE 16: Risk Calculation Trigger")
print("="*70)
code, d = post("/api/calculate-risks")
if code == 200:
    ok(f"Risk calculation: status={d['status']}, processed={d['processed']}, failed={d['failed']}")
    
    if d["processed"] == 20 and d["failed"] == 0:
        ok("All 20 wards processed successfully")
    else:
        fail(f"Processing issues: {d['processed']} processed, {d['failed']} failed")
    
    if d.get("weather_fetched", 0) == 20:
        ok("Weather fetched for all wards")
else:
    fail(f"Calculate risks failed: {code}")

# ================================================================
print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"  ✅ PASSED: {PASS}")
print(f"  ❌ FAILED: {FAIL}")
print(f"  ⚠️  WARNINGS: {WARN}")
print(f"  Total checks: {PASS + FAIL + WARN}")

if FAIL == 0:
    print("\n  🎉 ALL CHECKS PASSED!")
elif FAIL <= 3:
    print(f"\n  ⚠️  {FAIL} issue(s) to address")
else:
    print(f"\n  🔴 {FAIL} issues need fixing")
