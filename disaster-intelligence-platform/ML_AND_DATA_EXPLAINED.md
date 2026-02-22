# PRAKALP — ML & Data Architecture Explained (Simply)

> This document explains every ML and data component in PRAKALP, why we built it
> the way we did, and why we didn't use LLMs or ARIMA models.
> Written in plain language so anyone can follow along.

---

## Table of Contents

1. [The Core Idea — What Problem Are We Solving?](#1-the-core-idea)
2. [Our Two-Layer Risk System (The Heart of Everything)](#2-two-layer-risk-system)
3. [Layer 1 — The Formula-Based Calculator](#3-layer-1)
4. [Layer 2 — The XGBoost ML Model](#4-layer-2)
5. [How We Merge Both Layers (Fusion)](#5-fusion)
6. [Where Does the Data Come From?](#6-data-sources)
7. [The 48-Hour Forecast Engine](#7-forecast)
8. [Scenario Simulator (What-If Engine)](#8-scenarios)
9. [Cascading Risk Chains](#9-cascading)
10. [Historical Validation (Did Our Model Get It Right?)](#10-validation)
11. [Resource Allocation Optimizer](#11-optimizer)
12. [River Monitoring](#12-rivers)
13. [The Full Data Flow (Start to Finish)](#13-data-flow)
14. [Why Not LLMs (ChatGPT-like models)?](#14-why-not-llms)
15. [Why Not ARIMA (Time-Series Models)?](#15-why-not-arima)
16. [Why Our Approach Is Better](#16-why-better)

---

## 1. The Core Idea — What Problem Are We Solving? <a name="1-the-core-idea"></a>

Imagine you're the Pune disaster manager. It's monsoon season. You need to answer:

- **Which of the 20 wards is most likely to flood TODAY?**
- **How dangerous is it ON A SCALE OF 0-100?**
- **WHY is it dangerous?** (so you can explain to your boss)
- **What should I DO about it?** (send pumps? open shelters?)

That's what PRAKALP does. It takes in weather data, ward characteristics
(elevation, drainage, population), and historical patterns — and outputs a
risk score from 0 to 100 for each of the 20 Pune wards, every 30 minutes.

The tricky part: we need the answer to be **accurate** (ML is good at this)
AND **explainable** (formulas are good at this). So we use BOTH.

---

## 2. Our Two-Layer Risk System <a name="2-two-layer-risk-system"></a>

Think of it like getting a medical opinion:

- **Layer 1 = The experienced doctor** who looks at your symptoms and uses
  well-known medical guidelines to assess your risk. You can follow their
  reasoning step by step. (Our formula-based composite calculator)

- **Layer 2 = The AI scan** that looks at patterns in your data that the
  doctor might miss — subtle non-obvious combinations. It's more accurate
  for edge cases but harder to explain. (Our XGBoost ML model)

- **Final answer = The doctor considers BOTH** — their experience (60%) and the
  AI scan (40%) — to give you the most reliable result.

```
Final Risk = 60% × (Formula Result) + 40% × (ML Result)
```

Why 60/40 and not 50/50? Because in disaster management, you need to TRUST
and EXPLAIN the result. If the formula says "high risk because of heavy rain
+ low elevation + poor drainage", a disaster manager can act on that
confidently. The ML adds accuracy for tricky situations, but the formula is
the backbone.

---

## 3. Layer 1 — The Formula-Based Calculator <a name="3-layer-1"></a>

**File:** `app/services/risk_engine/composite.py`

This is the transparent, auditable layer. Every number can be traced back to
a specific input. No black boxes.

### 3.1 Flood Baseline Score (How Flood-Prone Is This Ward in General?)

```
Flood Baseline = 50% × Historical + 30% × Elevation + 20% × (1 - Drainage)
```

What each piece means:

| Factor | Weight | What It Measures | Simple Explanation |
|--------|--------|------------------|-------------------|
| Historical Frequency | 50% | How often has this ward flooded before? | Past flooding is the #1 predictor of future flooding. FEMA uses the same principle. |
| Elevation Vulnerability | 30% | How low-lying is this ward? | Water flows downhill. Lower wards flood more. Pune has a 120-meter west-to-east slope. |
| Drainage Weakness | 20% | How bad are the drains? | `1 - drainage_index`. Bad drains = water has nowhere to go. |

**Example:** Kasba Peth gets ~90/100 because it has flooded many times (high
historical), sits in a low river valley (low elevation), and has old drainage
infrastructure.

### 3.2 Heat Baseline Score (How Heat-Vulnerable Is This Ward?)

```
Heat Baseline = 50% × Historical Heatwave Days + 30% × Elderly Ratio + 20% × Population Density
```

| Factor | Weight | Why It Matters |
|--------|--------|----------------|
| Historical Heatwave Days | 50% | Wards that saw more hot days historically will likely see more in the future. |
| Elderly Ratio | 30% | Older people are far more vulnerable to heat. A ward with 20% elderly vs 8% elderly has very different risk. |
| Population Density | 20% | Dense urban areas trap heat (Urban Heat Island effect). More concrete = more heat. |

### 3.3 Flood EVENT Risk (What's Happening Right Now With Today's Weather?)

This is where live weather data comes in:

```
Flood Event Risk = 60% × Rainfall Score + 20% × 48-Hour Cumulative Score + 20% × Baseline Vulnerability
```

| Factor | Weight | What It Is |
|--------|--------|------------|
| Rainfall Intensity Score | 60% | How hard is it raining RIGHT NOW? This is the dominant factor. |
| Cumulative 48h Score | 20% | How much rain has fallen in the last 2 days? Ground gets saturated. |
| Baseline Vulnerability | 20% | The structural score from above — wards with bad drainage are always more at risk. |

**Rainfall scoring isn't linear.** We use IMD (India Meteorological Department
) ranges because 50mm of rain isn't just "5× worse" than 10mm — it's
qualitatively different (waterlogging begins):

| Rainfall (mm) | Score | IMD Category | What Happens |
|---------------|-------|-------------|--------------|
| < 2mm | 0.0 | No rain | Nothing |
| 2–20mm | 0–0.30 | Light rain | Streets wet, no problem |
| 20–50mm | 0.30–0.60 | Moderate rain | Some waterlogging |
| 50–100mm | 0.60–0.80 | Heavy rain | Significant flooding |
| 100–200mm | 0.80–1.00 | Very heavy | Like Pune 2019 (200mm, 21 deaths) |

### 3.4 Heat EVENT Risk (Is There a Heatwave Happening?)

```
Heat Event Risk = 55% × Temp Anomaly Score + 20% × Baseline Vulnerability + 25% × UHI Score
```

**What's UHI?** Urban Heat Island. Even if two wards share the same
temperature, a ward with more concrete, more people, and more elderly will
FEEL hotter. UHI captures this:

```
UHI Score = 35% × Concrete/Impervious + 25% × Population Density + 20% × Elderly % + 20% × (1 - Drainage)
```

**Temperature anomaly scoring** (how much hotter than normal?):

| Anomaly | Score | What It Means |
|---------|-------|---------------|
| < 3°C above normal | 0–0.10 | Normal daily variation. Not a heatwave. |
| 3–5°C above | 0.10–0.35 | Notable. Watch situation. |
| 5–8°C above | 0.35–0.70 | Significant heatwave. Warnings needed. |
| > 8°C above | 0.70–1.00 | Extreme. Like Pune April 2024 (43.2°C). |

### 3.5 Risk Delta (Is Things Getting Worse?)

```
Delta = Event Risk - Baseline Risk
Delta % = (Delta / Baseline) × 100
```

This tells you: "Hey, things just got significantly worse than normal!"

| Delta % | Alert Level | What It Means |
|---------|-------------|---------------|
| ≥ 40% | CRITICAL | Drop everything, activate emergency. |
| ≥ 20% | SURGE | Situation rapidly deteriorating. |
| ≥ 10% | Elevated | Keep watching, prepare resources. |
| ≤ -10% | Decreasing | Situation improving. |

**Why delta matters:** A ward sitting at risk 85 forever is already being
managed. But a ward jumping from 45 to 75 in one cycle needs IMMEDIATE
attention — that sudden change is what kills people.

---

## 4. Layer 2 — The XGBoost ML Model <a name="4-layer-2"></a>

**Files:** `app/ml/model.py` (prediction), `app/ml/train.py` (training)

### 4.1 What Is XGBoost? (Simple Version)

XGBoost is like a panel of 200 "mini-experts" (decision trees). Each one
looks at the data and makes a guess. Some might say: "Heavy rain + low
elevation? Probably flood." Others might catch subtler patterns: "Moderate
rain BUT the ground is already saturated from yesterday AND the drainage is
poor? Also flood."

The final prediction is all 200 experts voting together. It's extremely good
at structured/tabular data (numbers in rows and columns) — which is exactly
what we have.

### 4.2 What Features (Inputs) Does It Get?

11 features per ward:

```
1. rainfall_intensity      — How heavy is the rain right now?
2. cumulative_rainfall_48h — Total rain in last 2 days
3. elevation_m             — How high is the ward (meters above sea level)
4. mean_slope              — How steep is the terrain
5. population_density      — People per square km
6. infrastructure_density  — Hospitals, fire stations, roads (0-10 score)
7. historical_frequency    — How many times has it flooded before
8. drainage_index          — How good are the drains (0-1)
9. impervious_surface_pct  — Percentage of concrete/asphalt (can't absorb water)
10. low_lying_index        — How much of the ward is in a low area
11. elderly_ratio          — Percentage of population that's elderly
```

### 4.3 How Is It Trained? (Physics-Informed Synthetic Data)

**The problem:** We don't have thousands of labeled examples of "this ward
flooded on this day." Pune has maybe 5-10 major flood events in the data.
That's not enough for ML.

**Our solution:** Generate realistic synthetic training data using physics
rules. Think of it like a driving school simulator — it's not the real road,
but the physics (gravity, friction, steering) are realistic.

**For floods (2000 samples):**
1. Randomly generate weather conditions (rainfall, temperature, etc.)
2. 40% of samples are deliberately monsoon-heavy (because that's where floods
   happen)
3. For each sample, compute a "flood score" using physics:
   ```
   flood_score = 35% × rain + 20% × cumulative_rain + 20% × (1 - elevation)
               + 15% × (1 - drainage) + 10% × low_lying
   ```
4. Label it as "flood = yes" if score > 0.4 (targets ~25% positive rate)

**For heat (1500 samples):**
1. Season-stratified: 25% extreme summer (38-45°C), 30% mild, 45% monsoon
2. Temperature gates everything — if it's not hot, no heat risk
3. Label it as "heat event = yes" if combined score > 0.50

**Why this works:**
- The synthetic data ENCODES domain knowledge (low elevation + heavy rain = flood)
- XGBoost then learns the NON-LINEAR interactions that simple formulas can't express
- We validate against 5 REAL historical events to make sure it generalizes

### 4.4 XGBoost Settings

```python
n_estimators = 200       # 200 decision trees vote together
max_depth = 6            # Each tree can be up to 6 levels deep
learning_rate = 0.1      # Each tree corrects mistakes of previous trees slowly
subsample = 0.8          # Each tree sees 80% of data (prevents overfitting)
colsample_bytree = 0.8   # Each tree sees 80% of features (prevents overfitting)
```

Validated with **5-fold stratified cross-validation** — the model is tested
on data it hasn't seen 5 different times, measuring ROC-AUC, F1, precision,
and recall.

### 4.5 SHAP Explainability

Every prediction comes with SHAP (SHapley Additive exPlanations) values that
show WHY the model made that decision:

```
Kasba Peth flood probability: 0.82
  rainfall_intensity:    +0.23  (pushing risk UP)
  low_lying_index:       +0.18  (pushing risk UP)
  drainage_index:        +0.15  (poor drainage pushes UP)
  elevation_m:           +0.12  (low elevation pushes UP)
  historical_frequency:  +0.09  (past floods push UP)
```

This means: "The model thinks there's an 82% flood chance, mainly because
of heavy rain, the ward being low-lying, and poor drainage."

### 4.6 Heat Attenuation (A Clever Guard)

Without this, XGBoost might say "Kasba Peth has high heat risk" even on a
cool February day — just because it has dense population and elderly people.

We fix this with attenuation — scale down the ML heat prediction based on
ACTUAL temperature:

| Actual Temperature Anomaly | ML Output Is Multiplied By |
|----------------------------|---------------------------|
| < 1°C above normal | × 0.05 (basically zero — it's not hot!) |
| 1-3°C above | × 0.15 (slight concern) |
| 3-5°C above | × 0.40 (notable) |
| 5-8°C above | × 0.70 (real heatwave) |
| ≥ 8°C above | × 1.00 (full weight — extreme heat) |

This ensures the ML model can't cry wolf during cool weather.

### 4.7 Fallback (Model Not Available?)

If the XGBoost model files aren't loaded (first run, corruption, etc.), the
system DOESN'T crash. It falls back to rule-based heuristics:

```
Fallback flood probability =
  + 0.40 if rainfall > 50mm
  + 0.25 if cumulative > 150mm
  + up to 0.15 for low elevation
  + up to 0.10 for poor drainage
  + up to 0.10 for low-lying areas
```

The system NEVER fails silently — it degrades gracefully.

---

## 5. How We Merge Both Layers (Fusion) <a name="5-fusion"></a>

**File:** `app/services/risk_engine/final_risk.py`

```
Final Flood Risk = 60% × Composite Flood Event Risk + 40% × (ML Flood Probability × 100)
Final Heat Risk  = 60% × Composite Heat Event Risk  + 40% × (ML Heat Probability × 100)
Final Combined   = max(Final Flood, Final Heat)
```

### Neighbor Spillover

After computing each ward's risk, we check: does any ADJACENT ward have risk
≥ 80? If yes, add 5% to this ward's risk.

```
If neighbor risk ≥ 80 → this ward's risk += this ward's risk × 5%
```

**Why?** Water doesn't respect ward boundaries. If Kasba Peth is flooding,
the water will flow into Shivajinagar next door.

How we detect neighbors:
- **PostGIS** `ST_Touches` (if using PostgreSQL — geometrically adjacent)
- **Fallback:** Haversine distance between centroids < 3 km

### Confidence Score

Every risk score comes with a confidence rating:

```
Confidence = 40% × Data Completeness + 30% × ML Confidence + 30% × Weather Available
```

- **Data completeness:** Does this ward have all fields filled? (elevation,
  drainage, population, etc.)
- **ML confidence:** How sure was XGBoost? (`|probability - 0.5| × 2` — a
  prediction of 0.95 is very confident, 0.52 is basically a coin flip)
- **Weather available:** Do we have fresh weather data?

This tells decision-makers: "This ward's risk is 72, and we're 85% confident
in that number." vs "Risk is 72, but we're only 45% confident — data might
be stale."

### Risk Categories

| Score Range | Category | Color |
|-------------|----------|-------|
| 0–30 | Low | Green |
| 30–60 | Moderate | Yellow |
| 60–80 | High | Orange |
| 80–100 | Critical | Red |

---

## 6. Where Does the Data Come From? <a name="6-data-sources"></a>

### 6.1 Weather Data — Open-Meteo API

**File:** `app/services/weather_service.py`

- **Source:** Open-Meteo (free, no API key required, global coverage)
- **What we fetch:** Temperature, humidity, rainfall, wind speed, pressure —
  both current (hourly) and forecast (48 hours ahead, 7 days)
- **Frequency:** Every 15 minutes (via background scheduler)
- **Concurrency:** Fetches all 20 wards in parallel using `asyncio.Semaphore(5)`
  (5 at a time to not overwhelm the API)
- **Caching:** Results stored in Redis so we don't hammer the API. If the API
  is down, we use cached data.

What we compute from raw weather:
- `current_rainfall_mm` — rain right now
- `rainfall_forecast_48h_mm` — total expected rain in next 2 days
- `rainfall_forecast_7d_mm` — total expected rain in next week
- `max_rainfall_intensity_mm_h` — peak rain rate (important for flash floods)
- `temp_anomaly_c` — how much hotter/cooler than this ward's historical average
- `weather_condition` — classified as: heavy_rain (>50mm), moderate_rain (>10mm),
  light_rain (>2mm), extreme_heat (>42°C), heatwave (>38°C), hot (>35°C), clear

### 6.2 Ward Data — Pre-loaded from Census + Geographic Sources

**File:** `app/services/ward_data_service.py`

20 Pune wards (W001-W020) with:
- Real Census 2011 populations (98,000 to 350,000)
- Real centroid coordinates (latitude/longitude)
- Drainage index (0-1 scale, estimated from ward infrastructure)
- Impervious surface percentage (how much concrete)
- Historical flood frequency, heatwave days
- Elevation (from SRTM 30m DEM or topographic model)
- Elderly ratio, population density

### 6.3 Elevation Data — SRTM DEM

**File:** `app/services/dem_processor.py`

- **Source:** SRTM 30-meter resolution Digital Elevation Model (satellite data)
- Extracts elevation, slope, and low-lying index around each ward centroid
- If DEM file not available, uses a **topographic fallback model** specific to
  Pune: west-to-east gradient of ~120m over 20km, river valley depressions,
  hill adjustments for Vetal Hill and Parvati Hill

### 6.4 Infrastructure Data — OpenStreetMap (OSM)

**File:** `app/services/osm_service.py`

- **Source:** Overpass API (queries OpenStreetMap)
- Counts hospitals, clinics, fire stations, police stations, schools, shelters
  within 2 km of each ward centroid
- Measures road density (km of roads per sq km)
- Computes infrastructure density score (0-10):
  ```
  Score = Medical (up to 3) + Emergency (up to 2) + Shelters (up to 2) + Roads (up to 3)
  ```

### 6.5 Background Scheduler

**File:** `app/jobs/scheduler.py`

| Job | Runs Every | What It Does |
|-----|-----------|-------------|
| Weather ingestion | 15 minutes | Fetches fresh weather for all 20 wards |
| Risk recompute | 30 minutes | Full pipeline: weather → composite → ML → fusion → save to DB |
| Data cleanup | Daily | Deletes risk scores older than 30 days |

### 6.6 Caching (Redis)

**File:** `app/db/cache.py`

- Stores weather data, risk scores, and OSM data in Redis (fast in-memory store)
- Prevents unnecessary API calls
- If Redis is unavailable, the system continues without caching (no crash)

---

## 7. The 48-Hour Forecast Engine <a name="7-forecast"></a>

**File:** `app/services/forecast_engine.py`

Not just "what's the risk now?" but "what will the risk be in 6 hours? 12?
24? 48?"

### How It Works

1. Take the weather forecast data (from Open-Meteo) for the next 48 hours
2. At each of 11 timesteps (`[0, 3, 6, 9, 12, 18, 24, 30, 36, 42, 48]` hours),
   build a weather snapshot
3. Run the composite risk calculator (Layer 1) for each timestep
4. Result: a timeline showing how risk changes over the next 2 days

### What It Detects

- **Peak risk:** When is the worst moment? ("Peak flood risk at hour 18")
- **Danger windows:** When does risk exceed 65? ("Danger from hour 12 to hour 30")
- **Time to critical:** How many hours until risk > 80?
- **Trend:** Rising, falling, or stable?

### Alert Levels (per timestep)

| Risk Score | Level | What It Means |
|------------|-------|---------------|
| < 30 | Normal | All clear |
| 30–50 | Advisory | Be aware |
| 50–65 | Watch | Prepare resources |
| 65–80 | Warning | Start activating emergency plans |
| ≥ 80 | Emergency | Full emergency response |

**Why this matters:** Static risk maps only show "now." The forecast shows
"WHEN it gets dangerous" — so you can pre-position water pumps and evacuation
buses 6-12 hours BEFORE the flood, not scramble during it.

---

## 8. Scenario Simulator (What-If Engine) <a name="8-scenarios"></a>

**File:** `app/services/risk_engine/scenario.py`

"What if rainfall doubles?"
"What if there's a +6°C heatwave?"
"What if we improve drainage by 30%?"

### 8 Pre-Built Scenarios

| Preset | What It Simulates |
|--------|------------------|
| Heavy Rainfall | 2× normal rain |
| Extreme Rainfall | 3.5× normal rain |
| Cloudburst | 5× normal rain |
| Moderate Heatwave | +3°C above normal |
| Severe Heatwave | +6°C above normal |
| Compound Disaster | 2.5× rain + 2°C heat |
| Improved Drainage | Drainage improved by 30% |
| Infrastructure Failure | 50% of infrastructure down |

Plus custom sliders for any combination.

### How It Works (Important — We Just Fixed This)

**The key principle: same formula for baseline AND scenario.**

1. Compute BASELINE event risk using CURRENT weather (unmodified)
2. Compute SCENARIO event risk using MODIFIED weather (e.g., rain × 3)
3. Delta = Scenario - Baseline

This guarantees that if all sliders are at neutral (1.0× rain, 0°C temp),
the delta is exactly ZERO. (Before our fix, it was comparing two completely
different formulas and showing nonsense results.)

### Clever Details

**Non-linear rainfall sensitivity:**
```
sensitivity = 1.0 + 0.3 × (rain_multiplier - 1)^1.2
```
Doubling rainfall more than doubles flood risk — because drainage capacity
is overwhelmed non-linearly.

**Dry-season handling:** In February (no rain), `3× 0mm = 0mm`. That's
useless. So when actual rain < 2mm and the user simulates higher rain, we
inject a representative base value (10mm) to make the scenario meaningful.

**WardProxy pattern:** Scenarios create temporary copies of ward data. The
real database is NEVER modified by scenarios.

---

## 9. Cascading Risk Chains <a name="9-cascading"></a>

**File:** `app/services/risk_engine/cascading_risk.py`

Real disasters don't happen in isolation. They cascade.

### 4 Pune-Specific Chains

**1. Khadakwasla Dam Release (Multiplier: 2.2×)**
```
Dam release → River surge (2h) → Urban flooding (4h) → Infrastructure collapse (8h)
```
The dam upstream of Pune has been released during floods before. When
released, the river surges, flooding the downstream urban area, which then
overwhelms infrastructure.

**2. Power Grid Cascade (Multiplier: 2.0×)**
```
Grid overload → Partial blackout (1h) → Full blackout (3h) → Emergency (6h)
```
During heatwaves, everyone runs AC → grid overloads → blackout → no cooling →
heat deaths multiplied.

**3. Monsoon Compound (Multiplier: 2.5×)**
```
Heavy rain → Drain overflow (1h) → Road flooding (3h) → Traffic gridlock (5h) → Evacuation blocked (8h)
```
The deadliest chain: flooding blocks roads, gridlock prevents evacuation,
people are trapped.

**4. Landslide-Flood (Multiplier: 3.0×)**
```
Soil saturation → Slope failure (2h) → Debris flow (4h) → Flash flood (6h)
```
On Pune's western hills, saturated soil gives way to landslides that dam
streams, which then burst.

Each stage has a `delay_hours` (how long until it triggers) and an
`amplification` factor (how much worse it makes things).

---

## 10. Historical Validation <a name="10-validation"></a>

**File:** `app/services/historical_validator.py`

"Does our model actually work?" We test it against 5 REAL Pune disasters:

| Event | Date | Type | What Happened |
|-------|------|------|---------------|
| Pune 2019 Flood | Sep 25, 2019 | Flood | 200mm rain, 21 deaths, massive flooding |
| Pune 2020 Flood | Oct 14, 2020 | Flood | Severe waterlogging across city |
| Pune 2023 Flash Flood | Jul 12, 2023 | Flood | Flash flooding |
| Pune 2024 Heatwave | Apr 28, 2024 | Heat | 43.2°C extreme heat |
| Pune 2024 Monsoon | Sep 26, 2024 | Flood | Recent monsoon flooding |

### How Validation Works

1. Fetch the ACTUAL weather from that day (from Open-Meteo's historical
   archive — real recorded data, not simulated)
2. Adjust weather per ward: wards with poor drainage or low elevation
   experience worse effects from the same rainfall
3. Run our risk calculator on that historical weather
4. If our model predicts risk ≥ 55 → "we predicted this ward would flood"
5. Compare against which wards ACTUALLY flooded
6. Compute: accuracy, precision, recall, F1 score

**Why this is gold:** We're not just testing the ML model in isolation.
We're testing the ENTIRE pipeline (weather processing → composite calculator
→ thresholds) against real disasters. If we correctly identify Kasba Peth as
high-risk during the 2019 flood, that builds genuine trust.

---

## 11. Resource Allocation Optimizer <a name="11-optimizer"></a>

**File:** `app/services/optimizer.py`

Once we know which wards are at risk, WHERE do we send pumps, buses, and
medical teams?

### Need Score Formula

```
risk_weight = (risk / 100)²    ← Quadratic: high risk gets MUCH more
need = risk_weight² × (70% risk + 30% population) × 100
```

**Why quadratic?** With linear scoring, a ward at risk 80 gets 2× the
resources of a ward at risk 40. But the ward at 80 is in MUCH more danger.
Quadratic makes it 4× instead — which better matches the urgency.

### 5 Resource Types

| Resource | Total Available | Good For Flood? | Good For Heat? |
|----------|----------------|-----------------|----------------|
| Water Pumps | 50 | YES (high) | NO (zero — never sent to heat-only wards) |
| Evacuation Buses | 30 | YES (high) | Somewhat |
| Relief Camps | 20 | YES (high) | YES (high) |
| Cooling Centers | 25 | NO (zero) | YES (high) |
| Medical Units | 15 | Somewhat | YES (high) |

**Key insight:** Pumps are NEVER allocated to wards where the primary hazard
is heat. Cooling centers are NEVER allocated to flood-only wards. The
optimizer respects the hazard-effectiveness matrix.

### Integer Allocation (Largest Remainder Method)

You can't send 2.7 buses somewhere. The optimizer uses the Largest Remainder
Method (same algorithm used in parliamentary seat allocation) to distribute
integer quantities that sum to exactly the total available.

### Gap Analysis

For each ward, we compute:
- **Ideal allocation** based on risk and population
- **Actual allocation** constrained by total available
- **Gap** = Ideal - Actual
- **Coverage %** = Actual / Ideal

This tells authorities: "We're at 60% coverage for water pumps citywide —
we need 30 more to fully protect all at-risk wards."

---

## 12. River Monitoring <a name="12-rivers"></a>

**File:** `app/services/river_monitor.py`

5 real Central Water Commission (CWC) stations on Pune's rivers:

| Station | River | Danger Level | Nearby Wards |
|---------|-------|-------------|--------------|
| Vithalwadi Bridge | Mutha | 8.5m | Kasba Peth, Shivajinagar, etc. |
| Aundh Bridge | Mula | 7.8m | Aundh, Baner, Balewadi |
| Sangam Bridge | Mula-Mutha | 9.0m | Deccan, Bibwewadi, etc. |
| Bund Garden Weir | Mula-Mutha | 8.0m | Camp, Koregaon Park |
| Mundhwa Bridge | Mula-Mutha | 7.5m | Mundhwa, Kharadi |

River levels are estimated from rainfall:
```
level = base_level + total_rainfall × 0.015 + 0.1 × sin(diurnal_cycle)
```

Flood stages: Normal → Alert → Warning → Danger → Extreme

When a station hits "danger", all nearby wards get advisories.

---

## 13. The Full Data Flow <a name="13-data-flow"></a>

Here's how everything connects, start to finish:

```
STEP 1: DATA IN
  Open-Meteo API ──→ Weather Service ──→ Redis Cache
  SRTM DEM ──→ DEM Processor ──→ Elevation/slope per ward
  OpenStreetMap ──→ OSM Service ──→ Infrastructure scores
  Census data ──→ Ward Data Service ──→ Population, demographics

STEP 2: LAYER 1 (COMPOSITE)
  Weather + Ward features ──→ CompositeRiskCalculator
    ├── Flood baseline (structural vulnerability)
    ├── Flood event risk (weather-driven)
    ├── Heat baseline (demographic vulnerability)
    └── Heat event risk (temperature-driven)

STEP 3: LAYER 2 (ML)
  11 features ──→ XGBoost model
    ├── Flood probability + SHAP values
    └── Heat probability (× attenuation) + SHAP values

STEP 4: FUSION
  60% Composite + 40% ML × 100 ──→ Final Risk Score
  + Neighbor spillover (+5% if adjacent ward ≥ 80)
  + Confidence scoring
  + Risk category (low/moderate/high/critical)
  + Delta detection (surge/critical alerts)
  ──→ Saved to WardRiskScore table in database

STEP 5: DOWNSTREAM SYSTEMS (all feed from the fused risk)
  ├── 48-Hour Forecast (risk timeline per ward)
  ├── Scenario Simulator (what-if analysis)
  ├── Cascading Risk (chain reactions)
  ├── Resource Optimizer (where to send pumps/buses/etc.)
  ├── River Monitor (CWC station levels)
  ├── Evacuation Router (optimal shelter routes)
  ├── Alert Service (bilingual EN/MR notifications)
  ├── Decision Support (action plan for officials)
  └── Historical Validator (test against real events)

STEP 6: OUTPUT
  ──→ 30+ REST API endpoints
  ──→ React frontend dashboard
  ──→ Updates every 30 minutes automatically
```

---

## 14. Why Not LLMs (ChatGPT-like Models)? <a name="14-why-not-llms"></a>

This is a very fair question. LLMs are amazing — but they solve a DIFFERENT
problem. Here's why:

### 14.1 LLMs Solve the Wrong Problem

Our core task is:
> "Take 11 numbers (rainfall, elevation, drainage...) → output one number (risk 0-100)"

That's **tabular classification/regression**. It's like asking "what's
2 + 3?" — you don't need a language model for that.

LLMs are built for language: understanding text, generating paragraphs,
having conversations. Using an LLM for numerical risk scoring is like using
a chainsaw to cut paper — it technically works, but a pair of scissors is
better.

Academic research backs this up. A 2022 paper from researchers at Inria
("Why do tree-based models still outperform deep learning on tabular data?")
showed that for structured data in rows and columns, gradient-boosted trees
(like XGBoost) consistently beat neural networks, including transformers.

### 14.2 Speed

| Approach | Time Per Prediction | Cost |
|----------|-------------------|------|
| XGBoost | < 1 millisecond | Free (runs locally) |
| LLM API (GPT-4) | 1-5 seconds | $0.01-0.10 per call |
| Local LLM | 2-10 seconds | Needs expensive GPU |

Our pipeline runs every 30 minutes for 20 wards = 40 predictions per hour.
With an LLM that's fine cost-wise, but during a crisis you might recompute
every 5 minutes. And the 1-5 second latency means the dashboard feels sluggish.

XGBoost: 20 wards × <1ms = done in 20 milliseconds. Instant.

### 14.3 Explainability

When a disaster manager needs to justify to the Chief Minister why they
evacuated 50,000 people, they need AUDITABLE numbers.

**XGBoost + SHAP gives:**
```
Risk = 82. Top factors:
  - Rainfall intensity: +23 points
  - Low elevation: +18 points
  - Poor drainage: +15 points
```
This is mathematically verifiable. Anyone can check the formula.

**An LLM would give:**
> "Based on the current weather conditions and the ward's geographical
> characteristics, I assess the flood risk to be approximately high..."

That's a paragraph that SOUNDS intelligent but can't be verified. Was it
"approximately high" because of a real calculation, or because the model
saw similar-sounding text during training?

### 14.4 Hallucination Risk

LLMs sometimes confidently produce wrong answers. In a disaster system:
- LLM says "risk is low" when it should be 85 → people don't evacuate → deaths
- LLM says "risk is critical" when it's actually 30 → unnecessary panic, wasted resources

Our formula-based Layer 1 is DETERMINISTIC: same inputs ALWAYS produce same
outputs. No randomness, no temperature parameter, no hallucination.

### 14.5 Where LLMs WOULD Help (Future Features)

- **Natural language alerts:** "Heavy rainfall expected in Kasba Peth tonight.
  Move to higher floors. Nearest shelter: Bhavani Peth Community Hall."
- **Chatbot for citizens:** "Is my area safe?" → looks up risk → generates
  human-readable response
- **Summarizing situation reports** for officials
- **Translating alerts** into Marathi/Hindi naturally

These are all LANGUAGE tasks — which is what LLMs are for. But they sit ON
TOP of the risk engine, they don't REPLACE it.

---

## 15. Why Not ARIMA (Time-Series Models)? <a name="15-why-not-arima"></a>

ARIMA (Auto-Regressive Integrated Moving Average) is a classic time-series
forecasting model. Also a fair question. Here's why it doesn't fit:

### 15.1 ARIMA Needs Long, Regular Time Series — We Don't Have That

ARIMA needs hundreds of evenly-spaced observations of the SAME variable.
Like: "Daily flood risk for Ward X, every day for 3 years = 1,095 data points."

What we have: Maybe 5 major flood events in Pune across uneven years
(2019, 2020, 2023, 2024). That's not a time series — that's a handful of
scattered points. ARIMA can't work with that.

Think of it like this: ARIMA predicts tomorrow's stock price from the last
100 days of stock prices. We're trying to predict "will it flood today?"
from today's weather + the ward's permanent features. Completely different
problem structure.

### 15.2 Risk Depends on Features, Not Just Time

ARIMA models a single variable over time:

```
X(today) = some function of X(yesterday), X(day before), ...
```

It only looks at PAST VALUES of the thing you're predicting. It knows
nothing about:
- Today's rainfall (exogenous input)
- Ward elevation (cross-sectional feature)
- Drainage quality (infrastructure feature)
- Population density (demographic feature)

Our risk score depends on ALL of these. ARIMA would ignore everything
except the risk score's own history.

You could use ARIMAX (ARIMA with exogenous variables), but at that point
you're building a worse version of what XGBoost already does — because
XGBoost handles non-linear feature interactions naturally, while ARIMAX
assumes linear relationships.

### 15.3 ARIMA Assumes Stationarity — Disasters Are Non-Stationary

ARIMA requires that the statistical properties of your data (mean, variance)
stay stable over time. But flood events are:
- **Rare** — happening a few times per monsoon season
- **Extreme** — risk goes from 20 to 90 in hours when a cloudburst hits
- **Non-stationary** — climate change means floods are getting worse over years

The 2019 Pune flood (200mm in a few hours) is a tail event. ARIMA would
either:
- Treat it as an outlier and smooth it out (dangerous — misses the event)
- Overfit to it and predict floods constantly (wasteful — false alarms)

### 15.4 Our 48-Hour Forecast Already Handles Time

You might think: "But we DO have a forecast engine that predicts risk over
time — isn't that what ARIMA is for?"

No. Our forecast engine doesn't extrapolate from past risk values. It uses
actual weather forecast data:

| ARIMA approach | Our approach |
|----------------|-------------|
| "Risk was 30 yesterday, 35 today, so tomorrow might be ~40" | "Tomorrow's forecast says 80mm rain → I'll compute flood risk using that 80mm as input" |
| Extrapolation from past pattern | Physics-based calculation from forecast data |
| No idea WHY risk is changing | Knows exactly why: "rain expected to peak at hour 18" |

Our approach is fundamentally more CAUSAL. ARIMA extrapolates; we calculate
from predicted future weather.

### 15.5 When Would ARIMA Be Useful?

If we had 10+ years of daily ward-level risk scores AND wanted to detect
long-term seasonal patterns (e.g., "monsoon typically starts in Ward X on
June 8 ± 3 days"), ARIMA or seasonal decomposition could add value. That's
a future enhancement once we accumulate enough historical data from
PRAKALP's own operation.

---

## 16. Why Our Approach Is Better <a name="16-why-better"></a>

### Compared to Pure-ML Systems

| Aspect | Pure ML (Black Box) | PRAKALP (Dual Layer) |
|--------|-------------------|---------------------|
| Explainability | "The model says 78" (why?) | "78 because: 50% historical floods + 30% low elevation + 20% poor drainage, confirmed by ML" |
| Trust | Officials hesitate to act on unexplained numbers | Officials can verify and understand the reasoning |
| Failure mode | Model fails = no output | ML fails = formulas still work (graceful degradation) |
| Auditability | Can't replicate why a decision was made | Every factor is logged with weights |

### Compared to Pure-Formula Systems

| Aspect | Pure Formulas | PRAKALP (Dual Layer) |
|--------|--------------|---------------------|
| Non-linear interactions | Can't capture "rain + saturated soil + poor drainage" combo effect | XGBoost captures these naturally |
| Adaptability | Need to manually tune weights | ML weights learn from data |
| Edge cases | Misses unusual combinations | XGBoost handles novel feature combos |

### Compared to LLM-Based Systems

| Aspect | LLM Approach | PRAKALP |
|--------|-------------|---------|
| Accuracy on tabular data | Worse (proven by research) | Better (XGBoost excels here) |
| Speed | 1-5 seconds per call | < 1 millisecond |
| Cost | API calls cost money | Free (runs locally) |
| Determinism | Different answer each time | Same inputs → same outputs always |
| Hallucination risk | Real | Zero (formulas are deterministic) |

### Compared to ARIMA-Based Systems

| Aspect | ARIMA | PRAKALP |
|--------|-------|---------|
| Data requirement | 500+ time points needed | Works with limited historical data |
| Feature usage | Only past values of target | Uses 11 features (weather, terrain, demographics) |
| Causality | Extrapolation (correlation) | Calculation from forecast weather (causal) |
| Extreme events | Smoothed out or overfit | Handled naturally by piecewise scoring |

### The Overall Philosophy

PRAKALP isn't just a prediction system. It's a full **decision-support
pipeline**:

```
Predict → Explain → Forecast → Simulate → Optimize → Act
```

1. **Predict:** What's the risk right now? (dual-layer fusion)
2. **Explain:** Why? (SHAP + composite factor breakdown)
3. **Forecast:** When will it get worse? (48-hour timeline)
4. **Simulate:** What if it gets MUCH worse? (scenario engine)
5. **Optimize:** Where should we send resources? (optimizer)
6. **Act:** What exactly should we do? (decision support + alerts)

No single ML model — not XGBoost, not an LLM, not ARIMA — does all of this.
The value is in the ARCHITECTURE: how multiple specialized components work
together, each using the right tool for its specific job.

---

---

## 17. What Data Is Real vs Mock vs Estimated? <a name="17-real-vs-mock"></a>

A common question: "Is PRAKALP using real data or is it all fake?"
The honest answer is: **it's a mix**. Here is every data type categorised clearly.

---

### Real Data (fetched from actual live/archived sources)

| Data | Where It Comes From | How |
|------|-------------------|-----|
| Live weather (rainfall, temperature, humidity, wind) | Open-Meteo API | Fetched every 15 minutes via the weather service |
| Historical weather for validation events | Open-Meteo Archive API | Real recorded conditions for Sep 25 2019, Oct 14 2020, Jul 12 2023, Apr 28 2024, Sep 26 2024 |
| Ward names | Pune Municipal Corporation (PMC) | 20 real administrative wards of Pune |
| Ward populations | Census of India 2011 | Real figures per ward — range from 98,000 to 350,000 |
| Ward centroid coordinates | Geographic data | Real latitude/longitude for each ward |
| Historical disaster events | News records + NDMA reports | 5 real events with real dates, rainfall amounts, death tolls |
| River names and CWC station locations | Central Water Commission | Real rivers (Mula, Mutha, Mula-Mutha), real bridge names |
| Elevation (when DEM file is present) | SRTM 30-metre satellite (NASA) | Real topographic measurements |
| OSM infrastructure (when fetched) | OpenStreetMap Overpass API | Real hospital counts, road lengths, school locations |

These inputs are live and real. **Weather is the most important input to the
risk model**, and it is 100% real data from a live API.

---

### Estimated Data (based on real geography but not from official PMC datasets)

These values are grounded in reality but could not be pulled from a public
dataset — they were estimated using domain knowledge of Pune.

| Data | What We Did | What Would Make It Better |
|------|------------|--------------------------|
| Drainage index per ward (0–1) | Estimated based on known old vs new infrastructure. Kasba Peth (old city core) = lower, Baner (newer area) = higher. | PMC stormwater drain survey data |
| Impervious surface % | Estimated from urban density knowledge. Dense old wards ≈ 70–80%, newer peripheral wards ≈ 50–60%. | Satellite land-use classification (LULC) |
| Historical flood frequency per ward | Estimated from news reports (2014–2024). Not an official count. | PMC ward-level flood incident database |
| Elderly ratio | Estimated demographic ratios (8–18% range). | Ward-level Census 2011 demographic breakdown |
| Elevation fallback (when no DEM) | Topographic model: 120m west-to-east gradient across Pune, river valley depressions, Vetal Hill and Parvati Hill adjustments. Correct shape but not measured. | Actual SRTM DEM file |
| Shelter locations / capacities | Real Pune landmark names, but capacities are rough estimates. | PMC disaster shelter registry |

These are the ward "static features" used in the formulas and as XGBoost
inputs. They shape the structural baseline risk. Replacing them with official
PMC data would improve accuracy but wouldn't change how the system works.

---

### Synthetic / Mock Data

These are components that are built for demonstration and architecture
purposes. They are not intended to be real — but are designed so real data
can be plugged in without any code changes.

| Data | Why It's Synthetic | What Real Replacement Looks Like |
|------|-------------------|----------------------------------|
| ML training data (2,000 flood + 1,500 heat samples) | Ward-level labeled flood records don't exist publicly at this granularity in India. Generated using physics-informed rules. | Historical incident logs from NDRF/SDRF with ward-level impact data |
| River water levels | Simulated from rainfall: `level = base + rain × 0.015`. Station names are real; telemetry is not. | Live CWC river gauge API (real-time telemetry) |
| Resource inventory (50 pumps, 30 buses, etc.) | Made-up numbers to demonstrate the optimizer. | PMC Disaster Management Cell's actual equipment inventory |
| Road segments for evacuation routing | Simplified 8-segment network. | Full OSM road graph with real road IDs and flood-prone flags |
| Cascading risk timing (delay hours, amplification) | Conceptual models based on general disaster research. Not calibrated to real Pune incident timelines. | Post-incident analysis reports from real Pune disasters |
| Infrastructure density scores (fallback) | Preset values used when OSM hasn't been fetched for a ward. | Always online OSM fetching at startup |

---

### Summary at a Glance

```
WEATHER DATA       ████████████████  100% REAL (live API, every 15 min)
GEOGRAPHY/NAMES    ████████████████  100% REAL (Census, coordinates, PMC)
HISTORICAL EVENTS  ████████████████  100% REAL (dates, rainfall, impacts)
WARD FEATURES      ████████░░░░░░░░   50% ESTIMATED (drainage, impervious, elderly)
ELEVATION          ████████░░░░░░░░   50% REAL when DEM present / estimated otherwise
OSM INFRA          ████████░░░░░░░░   50% REAL when fetched / preset otherwise
ML TRAINING DATA   ░░░░░░░░░░░░░░░░  100% SYNTHETIC (physics-informed)
RIVER LEVELS       ░░░░░░░░░░░░░░░░  100% SIMULATED from rainfall
RESOURCES          ░░░░░░░░░░░░░░░░  100% MOCK
EVACUATION ROUTES  ░░░░░░░░░░░░░░░░  100% SIMPLIFIED
```

---

### Why Is This Still a Credible System?

Two reasons:

**1. The dominant real-time input (weather) is fully real.**
Weather is weighted 60% in the flood event formula and 55% in the heat
formula. The live Open-Meteo data is what drives the day-to-day risk
variation. If it's raining heavily in Pune right now, the system correctly
shows higher flood risk.

**2. The architecture is production-ready — the data slots are defined.**
Every estimated or mock value has a clearly defined slot in the code. Swap it
with real PMC data and the formulas, ML model, and all downstream systems
work identically — with better accuracy. This is the standard way research
prototypes scale to production: build the architecture right, progressively
replace estimates with real data.

For a university project or research prototype, this is the expected and
appropriate approach. Systems like IFLOWS-Mumbai (MCGM's real flood warning
system) took years and significant government data-sharing agreements to get
fully real ward-level data.

---

*PRAKALP v2.0.0 — Predictive Risk Assessment And Knowledge Analytics For Localized Preparedness*
