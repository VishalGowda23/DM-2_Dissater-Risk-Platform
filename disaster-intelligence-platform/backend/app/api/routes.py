"""
API Routes: Health, Wards, Risk, Scenarios, Optimizer, Auth, Admin
All endpoints with proper pagination, filtering, error handling
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from app.db.database import get_db
from app.db.config import settings
from app.db.cache import get_cached_risk, cache_risk_scores
from app.api.deps import PaginationParams, RiskFilterParams
from app.models.ward import Ward, WardRiskScore
from app.models.user import User
from app.models.audit_log import AuditLog
from app.services.auth import (
    create_access_token, create_refresh_token, verify_password,
    hash_password, get_current_user, require_auth, require_admin,
    require_operator, initialize_admin_user
)
from app.services.weather_service import WeatherIngestionService
from app.services.risk_engine.final_risk import final_risk_calculator
from app.services.risk_engine.scenario import scenario_engine, ScenarioParameters
from app.services.optimizer import resource_allocator
from app.services.ward_data_service import initialize_wards, update_ward_osm_data
from app.services.osm_service import osm_service
from app.services.forecast_engine import forecast_engine
from app.services.historical_validator import historical_validator
from app.services.river_monitor import river_monitor
from app.services.risk_engine.cascading_risk import cascading_engine
from app.services.alert_service import alert_service
from app.services.evacuation_router import evacuation_router
from app.services.decision_support import decision_support

logger = logging.getLogger(__name__)


# ==================== HEALTH ROUTES ====================
health_router = APIRouter(tags=["Health"])


@health_router.get("/")
async def root():
    """API root information"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "wards": "/api/wards",
            "risk": "/api/risk",
            "scenarios": "/api/scenarios",
            "optimize": "/api/optimize",
            "docs": "/docs",
        },
    }


@health_router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Service health check with dependency status"""
    health = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.APP_VERSION,
        "services": {}
    }

    # Check database
    try:
        from sqlalchemy import text as sa_text
        db.execute(sa_text("SELECT 1"))
        health["services"]["database"] = "connected"
    except Exception:
        health["services"]["database"] = "disconnected"
        health["status"] = "degraded"

    # Check PostGIS
    try:
        from app.db.database import check_postgis
        if check_postgis():
            health["services"]["postgis"] = "enabled"
        else:
            health["services"]["postgis"] = "unavailable"
    except Exception:
        health["services"]["postgis"] = "unavailable"

    # Check Redis
    try:
        from app.db.cache import _is_redis_available
        if _is_redis_available():
            health["services"]["redis"] = "connected"
        else:
            health["services"]["redis"] = "disconnected"
    except Exception:
        health["services"]["redis"] = "disconnected"

    # Check ML model
    try:
        from app.ml.model import ml_model
        health["services"]["ml_model"] = "loaded" if ml_model.is_loaded else "fallback_mode"
    except Exception:
        health["services"]["ml_model"] = "unavailable"

    # Ward count
    try:
        ward_count = db.query(Ward).count()
        health["data"] = {"wards_loaded": ward_count}
    except Exception:
        health["data"] = {"wards_loaded": 0}

    return health


# ==================== WARD ROUTES ====================
ward_router = APIRouter(prefix="/api/wards", tags=["Wards"])


@ward_router.get("")
async def list_wards(
    db: Session = Depends(get_db),
    pagination: PaginationParams = Depends(),
):
    """List all wards with pagination"""
    total = db.query(Ward).count()
    wards = db.query(Ward).offset(pagination.offset).limit(pagination.limit).all()

    return {
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "wards": [w.to_dict() for w in wards],
    }


@ward_router.get("/{ward_id}")
async def get_ward(ward_id: str, db: Session = Depends(get_db)):
    """Get single ward with latest risk score"""
    ward = db.query(Ward).filter(Ward.ward_id == ward_id).first()
    if not ward:
        raise HTTPException(status_code=404, detail=f"Ward {ward_id} not found")

    result = ward.to_dict()

    # Attach latest risk score
    latest_risk = db.query(WardRiskScore).filter(
        WardRiskScore.ward_id == ward_id
    ).order_by(WardRiskScore.timestamp.desc()).first()

    if latest_risk:
        result["risk_score"] = latest_risk.to_dict()

    return result


# ==================== RISK ROUTES ====================
risk_router = APIRouter(prefix="/api/risk", tags=["Risk Assessment"])


@risk_router.get("")
async def get_risk_scores(
    db: Session = Depends(get_db),
    filters: RiskFilterParams = Depends(),
    pagination: PaginationParams = Depends(),
):
    """Get current risk scores — returns risk_data matching frontend RiskData type"""
    from sqlalchemy import func
    latest_ids = db.query(
        func.max(WardRiskScore.id).label("max_id")
    ).group_by(WardRiskScore.ward_id).subquery()

    query = db.query(WardRiskScore).join(
        latest_ids, WardRiskScore.id == latest_ids.c.max_id
    )

    # Apply filters
    if filters.ward_id:
        query = query.filter(WardRiskScore.ward_id == filters.ward_id)
    if filters.risk_category:
        query = query.filter(WardRiskScore.risk_category == filters.risk_category)
    if filters.min_risk is not None:
        query = query.filter(WardRiskScore.final_combined_risk >= filters.min_risk)

    # Sort
    sort_col = getattr(WardRiskScore, filters.sort_by, WardRiskScore.final_combined_risk)
    if filters.sort_order == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    total = query.count()
    scores = query.offset(pagination.offset).limit(pagination.limit).all()

    # Build risk_data matching frontend RiskData interface
    risk_data = []
    for s in scores:
        ward = db.query(Ward).filter(Ward.ward_id == s.ward_id).first()
        risk_data.append({
            "ward_id": s.ward_id,
            "ward_name": ward.name if ward else s.ward_id,
            "population": ward.population if ward else 0,
            "centroid": {
                "lat": ward.centroid_lat if ward else 0,
                "lon": ward.centroid_lon if ward else 0,
            },
            "flood": {
                "baseline": round(s.flood_baseline_risk or 0, 2),
                "event": round(s.flood_event_risk or 0, 2),
                "delta": round(s.flood_risk_delta or 0, 2),
                "delta_pct": round(s.flood_risk_delta_pct or 0, 2),
            },
            "heat": {
                "baseline": round(s.heat_baseline_risk or 0, 2),
                "event": round(s.heat_event_risk or 0, 2),
                "delta": round(s.heat_risk_delta or 0, 2),
                "delta_pct": round(s.heat_risk_delta_pct or 0, 2),
            },
            "top_hazard": s.top_hazard or "none",
            "top_risk_score": round(s.final_combined_risk or 0, 2),
        })

    return {
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "risk_data": risk_data,
        "timestamp": datetime.now().isoformat(),
    }


@risk_router.get("/summary")
async def get_risk_summary(db: Session = Depends(get_db)):
    """City-wide risk summary with aggregate statistics"""
    from sqlalchemy import func

    latest_ids = db.query(
        func.max(WardRiskScore.id).label("max_id")
    ).group_by(WardRiskScore.ward_id).subquery()

    scores = db.query(WardRiskScore).join(
        latest_ids, WardRiskScore.id == latest_ids.c.max_id
    ).all()

    if not scores:
        return {"message": "No risk scores computed yet. Run /api/calculate-risks first."}

    flood_risks = [s.final_flood_risk or 0 for s in scores]
    heat_risks = [s.final_heat_risk or 0 for s in scores]
    combined_risks = [s.final_combined_risk or 0 for s in scores]

    critical = [s for s in scores if s.risk_category == "critical"]
    high = [s for s in scores if s.risk_category == "high"]
    surge = [s for s in scores if s.surge_alert]
    critical_alerts = [s for s in scores if s.critical_alert]

    return {
        "total_wards": len(scores),
        "average_risks": {
            "flood": round(sum(flood_risks) / len(flood_risks), 2),
            "heat": round(sum(heat_risks) / len(heat_risks), 2),
            "combined": round(sum(combined_risks) / len(combined_risks), 2),
        },
        "max_risks": {
            "flood": round(max(flood_risks), 2),
            "heat": round(max(heat_risks), 2),
            "combined": round(max(combined_risks), 2),
        },
        "risk_distribution": {
            "critical": len(critical),
            "high": len(high),
            "moderate": len([s for s in scores if s.risk_category == "moderate"]),
            "low": len([s for s in scores if s.risk_category == "low"]),
        },
        "alerts": {
            "surge_alerts": len(surge),
            "critical_alerts": len(critical_alerts),
            "surge_wards": [s.ward_id for s in surge],
            "critical_wards": [s.ward_id for s in critical_alerts],
        },
        "critical_wards": [
            {"ward_id": s.ward_id, "risk": round(s.final_combined_risk or 0, 2), "hazard": s.top_hazard}
            for s in sorted(scores, key=lambda x: x.final_combined_risk or 0, reverse=True)[:5]
        ],
        "last_computed": max(s.timestamp for s in scores).isoformat() if scores else None,
    }


@risk_router.get("/explain/{ward_id}")
async def explain_risk(
    ward_id: str,
    hazard: str = Query("flood", description="Hazard type: flood or heat"),
    db: Session = Depends(get_db),
):
    """Detailed risk explanation for a ward with SHAP values and recommendations"""
    ward = db.query(Ward).filter(Ward.ward_id == ward_id).first()
    if not ward:
        raise HTTPException(status_code=404, detail=f"Ward {ward_id} not found")

    if hazard not in ("flood", "heat"):
        raise HTTPException(status_code=400, detail="Hazard must be 'flood' or 'heat'")

    latest = db.query(WardRiskScore).filter(
        WardRiskScore.ward_id == ward_id
    ).order_by(WardRiskScore.timestamp.desc()).first()

    if not latest:
        raise HTTPException(status_code=404, detail=f"No risk score computed for ward {ward_id}")

    explanation = {
        "ward_id": ward_id,
        "ward_name": ward.name,
        "hazard": hazard,
        "risk_score": latest.to_dict(),
        "top_drivers": latest.top_drivers or [],
        "shap_values": (latest.shap_values or {}).get(hazard),
        "recommendations": latest.recommendations or [],
        "ward_characteristics": {
            "elevation_m": ward.elevation_m,
            "drainage_index": ward.drainage_index,
            "population_density": ward.population_density,
            "elderly_ratio": ward.elderly_ratio,
            "infrastructure_density": ward.infrastructure_density,
            "historical_flood_frequency": ward.historical_flood_frequency,
            "data_completeness": ward.data_completeness,
        },
        "confidence": latest.confidence_score,
        "uncertainty": latest.uncertainty_score,
    }

    return explanation


# ==================== CALCULATE RISKS ====================
compute_router = APIRouter(prefix="/api", tags=["Computation"])


@compute_router.post("/calculate-risks")
async def calculate_all_risks(db: Session = Depends(get_db)):
    """
    Full risk calculation pipeline for all wards:
    1. Fetch weather data
    2. Compute Layer 1 (Composite)
    3. Compute Layer 2 (ML)
    4. Fuse to Final Risk
    5. Apply neighbor spillover
    6. Save to database
    """
    wards = db.query(Ward).all()
    if not wards:
        raise HTTPException(status_code=404, detail="No wards found. Initialize data first.")

    # Fetch weather for all wards
    weather_service = WeatherIngestionService()
    weather_results = await weather_service.ingest_for_wards(wards)
    weather_data = weather_results.get("wards", {})

    processed = 0
    failed = 0

    for ward in wards:
        try:
            ward_weather = weather_data.get(ward.ward_id)

            # Full dual-layer risk calculation
            risk_data = final_risk_calculator.calculate_full_risk(
                ward, wards, ward_weather, db
            )

            # Create risk score record
            risk_score = WardRiskScore(
                ward_id=ward.ward_id,
                **{k: v for k, v in risk_data.items() if hasattr(WardRiskScore, k)}
            )
            db.add(risk_score)

            # Cache the result
            cache_risk_scores(ward.ward_id, risk_data)

            processed += 1

        except Exception as e:
            logger.error(f"Risk calc failed for {ward.ward_id}: {e}")
            failed += 1

    db.commit()

    return {
        "status": "completed",
        "processed": processed,
        "failed": failed,
        "weather_fetched": weather_results.get("success", 0),
        "timestamp": datetime.now().isoformat(),
    }


@compute_router.post("/ingest/weather")
async def ingest_weather(db: Session = Depends(get_db)):
    """Trigger weather data ingestion for all wards"""
    wards = db.query(Ward).all()
    service = WeatherIngestionService()
    result = await service.ingest_for_wards(wards)

    return {
        "status": "completed",
        "total_wards": len(wards),
        "successful": result.get("success", 0),
        "failed": result.get("failed", 0),
        "timestamp": datetime.now().isoformat(),
    }


@compute_router.post("/ingest/osm")
async def ingest_osm(db: Session = Depends(get_db)):
    """Trigger OSM infrastructure data fetch for all wards"""
    wards = db.query(Ward).all()
    results = await osm_service.batch_fetch_all_wards(wards)

    updated = 0
    for ward_id, data in results.items():
        try:
            update_ward_osm_data(db, ward_id, data)
            updated += 1
        except Exception as e:
            logger.error(f"OSM update failed for {ward_id}: {e}")

    return {
        "status": "completed",
        "wards_updated": updated,
        "timestamp": datetime.now().isoformat(),
    }


@compute_router.post("/initialize")
async def initialize_data(db: Session = Depends(get_db)):
    """Initialize database with Pune ward data"""
    result = initialize_wards(db)
    initialize_admin_user(db)
    return {"status": "initialized", **result}


# ==================== SCENARIO ROUTES ====================
scenario_router = APIRouter(prefix="/api", tags=["Scenario Simulation"])


@scenario_router.get("/scenarios")
async def list_scenarios():
    """List available scenario presets"""
    return {
        "scenarios": scenario_engine.get_available_scenarios(),
        "custom_params": {
            "rain_multiplier": "float, default 1.0",
            "temperature_increase": "float (°C), default 0.0",
            "infrastructure_failure_factor": "float 0-1, default 0.0",
            "drainage_improvement": "float 0-1, default 0.0",
            "population_growth_pct": "float (%), default 0.0",
        },
    }


@scenario_router.post("/scenario/run")
@scenario_router.post("/scenario")  # alias for frontend
async def run_scenario(request: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Run scenario simulation
    Handles both direct params and frontend nested custom_params format
    """
    wards = db.query(Ward).all()
    if not wards:
        raise HTTPException(status_code=404, detail="No wards. Initialize data first.")

    scenario_key = request.get("scenario_key")
    custom_params = None

    # Handle frontend nested custom_params format
    frontend_params = request.get("custom_params", {})

    if scenario_key and scenario_key != "custom":
        # Use a preset scenario
        pass
    else:
        # Custom scenario — map frontend field names to backend field names
        custom_params = ScenarioParameters(
            rain_multiplier=frontend_params.get("rainfall_multiplier",
                request.get("rain_multiplier", 1.0)),
            temperature_increase=frontend_params.get("temp_anomaly_addition",
                request.get("temperature_increase", 0.0)),
            drainage_improvement=frontend_params.get("drainage_efficiency_multiplier",
                request.get("drainage_improvement", 0.0)),
            infrastructure_failure_factor=request.get("infrastructure_failure_factor", 0.0),
            population_growth_pct=frontend_params.get("population_growth_pct",
                request.get("population_growth_pct", 0.0)),
            custom_label=request.get("custom_label", "Custom Scenario"),
        )
        # Treat drainage_efficiency_multiplier as relative to 1.0
        # Frontend sends 0.5-1.5, we need 0-1 improvement value
        de_mult = frontend_params.get("drainage_efficiency_multiplier", 1.0)
        if de_mult > 1.0:
            custom_params.drainage_improvement = de_mult - 1.0  # e.g 1.3 -> 0.3
        elif de_mult < 1.0:
            # Low efficiency = infrastructure failure effect
            custom_params.infrastructure_failure_factor = max(
                custom_params.infrastructure_failure_factor, 1.0 - de_mult
            )
            custom_params.drainage_improvement = 0.0

        scenario_key = None  # ensure we use custom_params

    try:
        raw_result = scenario_engine.run_scenario_comparison(
            wards, scenario_key=scenario_key, custom_params=custom_params
        )

        # Transform response to match frontend ScenarioResult type
        ward_results = raw_result.get("ward_results", [])
        results = []
        total_flood_change = 0
        total_heat_change = 0
        newly_critical = 0

        for wr in ward_results:
            baseline_flood = wr["baseline"]["flood"]
            baseline_heat = wr["baseline"]["heat"]
            scenario_flood = wr["scenario_risk"]["flood"]
            scenario_heat = wr["scenario_risk"]["heat"]

            baseline_top = max(baseline_flood, baseline_heat)
            scenario_top = max(scenario_flood, scenario_heat)

            total_flood_change += wr["delta"]["flood"]
            total_heat_change += wr["delta"]["heat"]
            if scenario_top > 80 and baseline_top <= 80:
                newly_critical += 1

            results.append({
                "baseline": {
                    "ward_id": wr["ward_id"],
                    "ward_name": wr["ward_name"],
                    "population": 0,
                    "centroid": {"lat": 0, "lon": 0},
                    "flood": {
                        "baseline": baseline_flood,
                        "event": baseline_flood,
                        "delta": 0, "delta_pct": 0,
                    },
                    "heat": {
                        "baseline": baseline_heat,
                        "event": baseline_heat,
                        "delta": 0, "delta_pct": 0,
                    },
                    "top_hazard": "flood" if baseline_flood > baseline_heat else "heat",
                    "top_risk_score": round(baseline_top, 2),
                },
                "scenario": {
                    "ward_id": wr["ward_id"],
                    "ward_name": wr["ward_name"],
                    "population": 0,
                    "centroid": {"lat": 0, "lon": 0},
                    "flood": {
                        "baseline": scenario_flood,
                        "event": scenario_flood,
                        "delta": wr["delta"]["flood"],
                        "delta_pct": round(wr["delta"]["flood"] / max(baseline_flood, 0.01) * 100, 1),
                    },
                    "heat": {
                        "baseline": scenario_heat,
                        "event": scenario_heat,
                        "delta": wr["delta"]["heat"],
                        "delta_pct": round(wr["delta"]["heat"] / max(baseline_heat, 0.01) * 100, 1),
                    },
                    "top_hazard": "flood" if scenario_flood > scenario_heat else "heat",
                    "top_risk_score": round(scenario_top, 2),
                },
            })

        n = len(ward_results) or 1
        return {
            "scenario": raw_result.get("scenario", {}),
            "results": sorted(results, key=lambda r: r["scenario"]["top_risk_score"], reverse=True),
            "aggregate_impact": {
                "avg_flood_risk_change": round(total_flood_change / n, 1),
                "avg_heat_risk_change": round(total_heat_change / n, 1),
                "wards_newly_critical": newly_critical,
                "total_wards": n,
            },
            "timestamp": datetime.now().isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== OPTIMIZER ROUTES ====================
optimizer_router = APIRouter(prefix="/api", tags=["Resource Optimization"])


@optimizer_router.post("/optimize")
async def optimize_resources(request: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Optimize resource allocation based on current risk
    Handles frontend format: { resources: { pumps: 25, ... }, scenario: { use_delta: true } }
    """
    from sqlalchemy import func

    # Get latest risk scores
    latest_ids = db.query(
        func.max(WardRiskScore.id).label("max_id")
    ).group_by(WardRiskScore.ward_id).subquery()

    risk_scores = db.query(WardRiskScore).join(
        latest_ids, WardRiskScore.id == latest_ids.c.max_id
    ).all()

    if not risk_scores:
        raise HTTPException(status_code=404, detail="No risk scores. Run calculate-risks first.")

    # Build ward risk data
    wards_data = []
    for score in risk_scores:
        ward = db.query(Ward).filter(Ward.ward_id == score.ward_id).first()
        wards_data.append({
            "ward_id": score.ward_id,
            "ward_name": ward.name if ward else "",
            "population": ward.population if ward else 100000,
            "final_combined_risk": score.final_combined_risk,
            "risk_category": score.risk_category,
            "top_hazard": score.top_hazard,
            "surge_alert": score.surge_alert,
            "flood_risk_delta_pct": score.flood_risk_delta_pct,
            "heat_risk_delta_pct": score.heat_risk_delta_pct,
            "flood_risk": score.final_flood_risk or 0,
            "heat_risk": score.final_heat_risk or 0,
        })

    # Handle frontend nested scenario.use_delta format
    scenario_obj = request.get("scenario", {})
    use_delta = scenario_obj.get("use_delta", request.get("use_delta", True))

    # Map frontend resource keys to backend resource config
    frontend_resources = request.get("resources", {})
    RESOURCE_KEY_MAP = {
        "pumps": "water_pumps",
        "buses": "evacuation_buses",
        "relief_camps": "relief_camps",
        "cooling_centers": "cooling_centers",
        "medical_units": "medical_units",
    }

    custom_resources = None
    if frontend_resources:
        from app.services.optimizer import DEFAULT_RESOURCES
        custom_resources = {}
        for fe_key, count in frontend_resources.items():
            backend_key = RESOURCE_KEY_MAP.get(fe_key, fe_key)
            if backend_key in DEFAULT_RESOURCES:
                custom_resources[backend_key] = dict(DEFAULT_RESOURCES[backend_key])
                custom_resources[backend_key]["total"] = count
            else:
                # Unknown resource type, create a generic config
                custom_resources[backend_key] = {
                    "name": fe_key.replace("_", " ").title(),
                    "total": count,
                    "unit": "units",
                    "min_per_ward": 0,
                    "min_for_critical": 1,
                    "effectiveness": {"flood": 0.5, "heat": 0.5},
                }
    result = resource_allocator.optimize_allocation(
        wards_data, resources=custom_resources, use_delta=use_delta
    )

    # Transform response to match frontend OptimizationResult interface
    # Frontend expects: { ward_allocations, total_resources, total_allocated, summary, explanations }
    raw_allocations = result.get("allocations", {})

    # Build reverse key map for response
    REVERSE_KEY_MAP = {
        "water_pumps": "pumps",
        "evacuation_buses": "buses",
        "relief_camps": "relief_camps",
        "cooling_centers": "cooling_centers",
        "medical_units": "medical_units",
    }

    # Build total_resources and total_allocated dicts using frontend keys
    total_resources = {}
    total_allocated = {}
    for backend_key, alloc_data in raw_allocations.items():
        fe_key = REVERSE_KEY_MAP.get(backend_key, backend_key)
        total_resources[fe_key] = alloc_data["total_available"]
        total_allocated[fe_key] = alloc_data["total_allocated"]

    # Build ward_allocations: merge per-resource allocations into per-ward view
    ward_map = {}
    for wd in wards_data:
        ward_map[wd["ward_id"]] = {
            "ward_id": wd["ward_id"],
            "ward_name": wd["ward_name"],
            "population": wd["population"],
            "risk": {
                "flood": round(wd.get("flood_risk", 0), 2),
                "heat": round(wd.get("heat_risk", 0), 2),
                "delta": round(abs(wd.get("flood_risk_delta_pct", 0) or 0), 2),
            },
            "need_score": round(wd.get("need_score", 0), 2),
            "resources": {},
        }

    for backend_key, alloc_data in raw_allocations.items():
        fe_key = REVERSE_KEY_MAP.get(backend_key, backend_key)
        for wa in alloc_data.get("ward_allocations", []):
            wid = wa["ward_id"]
            if wid in ward_map:
                ward_map[wid]["resources"][fe_key] = {
                    "allocated": wa["allocated"],
                    "need_score": wa["need_score"],
                    "proportion": round(wa["allocated"] / max(alloc_data["total_available"], 1), 4),
                    "is_critical": wa.get("risk_category") in ["critical", "high"],
                }
                # Update need_score from allocation
                ward_map[wid]["need_score"] = max(ward_map[wid]["need_score"], wa["need_score"])

    # Sort by need_score descending
    ward_allocations = sorted(ward_map.values(), key=lambda w: w["need_score"], reverse=True)

    # Find highest need ward
    highest_need_ward = ward_allocations[0]["ward_id"] if ward_allocations else ""

    # Convert explanations list to dict
    raw_explanations = result.get("explanations", [])
    explanations_dict = {}
    for i, exp in enumerate(raw_explanations):
        explanations_dict[f"rule_{i+1}"] = exp

    raw_summary = result.get("summary", {})

    return {
        "timestamp": datetime.now().isoformat(),
        "scenario": {"use_delta": use_delta},
        "total_resources": total_resources,
        "total_allocated": total_allocated,
        "ward_allocations": ward_allocations,
        "explanations": explanations_dict,
        "summary": {
            "total_wards": raw_summary.get("total_wards", len(wards_data)),
            "critical_wards": raw_summary.get("critical_wards", 0),
            "highest_need_ward": highest_need_ward,
        },
    }


# ==================== AUTH ROUTES ====================
auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@auth_router.post("/login")
async def login(request: Dict[str, str], db: Session = Depends(get_db)):
    """Login and get JWT tokens"""
    username = request.get("username")
    password = request.get("password")

    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required")

    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    return {
        "access_token": create_access_token({"sub": user.username, "role": user.role}),
        "refresh_token": create_refresh_token({"sub": user.username}),
        "token_type": "bearer",
        "user": user.to_dict(),
    }


@auth_router.get("/me")
async def get_me(user: User = Depends(require_auth)):
    """Get current user info"""
    return user.to_dict()


# ==================== ADMIN ROUTES ====================
admin_router = APIRouter(prefix="/api/admin", tags=["Admin"])


@admin_router.put("/weights")
async def update_weights(
    request: Dict[str, Any],
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    """
    Admin: Update risk model weights
    Logged as audit event
    """
    old_weights = {
        "flood_baseline": dict(settings.FLOOD_BASELINE_WEIGHTS),
        "flood_event": dict(settings.FLOOD_EVENT_WEIGHTS),
        "heat_event": dict(settings.HEAT_EVENT_WEIGHTS),
    }

    # Update weights
    if "flood_baseline" in request:
        settings.FLOOD_BASELINE_WEIGHTS.update(request["flood_baseline"])
    if "flood_event" in request:
        settings.FLOOD_EVENT_WEIGHTS.update(request["flood_event"])
    if "heat_event" in request:
        settings.HEAT_EVENT_WEIGHTS.update(request["heat_event"])

    # Audit log
    audit = AuditLog(
        user_id=user.id,
        username=user.username,
        action="update_risk_weights",
        resource="risk_model_weights",
        details={"old": old_weights, "new": request},
    )
    db.add(audit)
    db.commit()

    return {
        "status": "updated",
        "weights": {
            "flood_baseline": dict(settings.FLOOD_BASELINE_WEIGHTS),
            "flood_event": dict(settings.FLOOD_EVENT_WEIGHTS),
            "heat_event": dict(settings.HEAT_EVENT_WEIGHTS),
        },
    }


@admin_router.get("/audit-log")
async def get_audit_log(
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
    pagination: PaginationParams = Depends(),
):
    """Get admin audit log"""
    total = db.query(AuditLog).count()
    logs = db.query(AuditLog).order_by(
        AuditLog.timestamp.desc()
    ).offset(pagination.offset).limit(pagination.limit).all()

    return {
        "total": total,
        "page": pagination.page,
        "logs": [log.to_dict() for log in logs],
    }


# ─── Feature: 48-Hour Temporal Forecasting ───────────────────────────────────
forecast_router = APIRouter(prefix="/api", tags=["Temporal Forecasting"])


@forecast_router.get("/forecast")
async def get_all_forecasts(db: Session = Depends(get_db)):
    """Get 48-hour risk forecast for all wards"""
    wards = db.query(Ward).all()
    if not wards:
        return {"error": "No wards found", "forecasts": []}

    # Fetch weather data for forecast
    weather_service = WeatherIngestionService()
    weather_result = await weather_service.ingest_for_wards(wards)
    weather_map = weather_result.get("wards", {})

    result = forecast_engine.compute_all_wards_forecast(wards, weather_map)
    return result


@forecast_router.get("/forecast/{ward_id}")
async def get_ward_forecast(ward_id: str, db: Session = Depends(get_db)):
    """Get detailed 48-hour forecast for a specific ward"""
    ward = db.query(Ward).filter(Ward.ward_id == ward_id).first()
    if not ward:
        raise HTTPException(status_code=404, detail=f"Ward {ward_id} not found")

    all_wards = db.query(Ward).all()

    weather_service = WeatherIngestionService()
    weather_result = await weather_service.ingest_for_wards([ward])
    ward_weather = weather_result.get("wards", {}).get(ward_id)

    result = forecast_engine.compute_ward_forecast(
        ward, ward_weather, all_wards
    )
    return result


# ─── Feature: Historical Event Validation ────────────────────────────────────
historical_router = APIRouter(prefix="/api", tags=["Historical Validation"])


@historical_router.get("/historical/events")
async def get_historical_events():
    """List all known disaster events available for validation"""
    return {
        "events": historical_validator.get_events(),
        "total": len(historical_validator.get_events()),
    }


@historical_router.post("/historical/validate/{event_id}")
async def validate_historical_event(event_id: str, db: Session = Depends(get_db)):
    """Run model validation against a known historical disaster event"""
    wards = db.query(Ward).all()
    if not wards:
        raise HTTPException(status_code=400, detail="No wards in database")

    try:
        result = await historical_validator.validate_event(event_id, wards)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Historical validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── Feature: River Level Monitoring ─────────────────────────────────────────
river_router = APIRouter(prefix="/api", tags=["River Monitoring"])


@river_router.get("/rivers")
async def get_river_levels(db: Session = Depends(get_db)):
    """Get current river levels for all CWC monitoring stations"""
    # Get weather data for realistic simulation
    wards = db.query(Ward).all()
    weather_service = WeatherIngestionService()
    weather_result = await weather_service.ingest_for_wards(wards)
    weather_map = weather_result.get("wards", {})

    return river_monitor.get_current_levels(weather_map)


@river_router.get("/rivers/impact")
async def get_river_impact(db: Session = Depends(get_db)):
    """Get which wards are impacted by current river levels"""
    wards = db.query(Ward).all()
    weather_service = WeatherIngestionService()
    weather_result = await weather_service.ingest_for_wards(wards)
    weather_map = weather_result.get("wards", {})

    levels = river_monitor.get_current_levels(weather_map)
    return river_monitor.get_ward_impact(levels)


# ─── Feature: Cascading / Compound Risk ──────────────────────────────────────
cascade_router = APIRouter(prefix="/api", tags=["Cascading Risk"])


@cascade_router.get("/cascading/chains")
async def get_cascade_chains():
    """List all defined cascade event chains"""
    return {
        "chains": cascading_engine.get_chains(),
        "total": len(cascading_engine.get_chains()),
    }


@cascade_router.post("/cascading/evaluate")
async def evaluate_cascade(
    request: Dict[str, Any],
    db: Session = Depends(get_db),
):
    """Evaluate a cascade chain for a specific ward or all wards"""
    chain_id = request.get("chain_id")
    ward_id = request.get("ward_id")

    if not chain_id:
        raise HTTPException(status_code=400, detail="chain_id required")

    wards = db.query(Ward).all()

    if ward_id:
        ward = db.query(Ward).filter(Ward.ward_id == ward_id).first()
        if not ward:
            raise HTTPException(status_code=404, detail=f"Ward {ward_id} not found")
        result = cascading_engine.evaluate_cascade_risk(
            chain_id, ward, baseline_flood=50, baseline_heat=50
        )
    else:
        result = cascading_engine.evaluate_all_cascades(wards)

    return result


# ─── Feature: Alert System ───────────────────────────────────────────────────
alert_router = APIRouter(prefix="/api", tags=["Alert System"])


@alert_router.get("/alerts")
async def get_alerts(db: Session = Depends(get_db)):
    """Generate and return current active alerts based on risk data"""
    wards = db.query(Ward).all()
    risk_data = []

    for ward in wards:
        scores = db.query(WardRiskScore).filter(
            WardRiskScore.ward_id == ward.ward_id
        ).order_by(WardRiskScore.timestamp.desc()).first()

        if scores:
            risk_data.append({
                "ward_id": ward.ward_id,
                "ward_name": ward.name,
                "population": ward.population or 0,
                "elderly_ratio": ward.elderly_ratio or 8,
                "top_hazard": scores.top_hazard or "flood",
                "top_risk_score": scores.final_combined_risk or 0,
                "final_combined_risk": scores.final_combined_risk or 0,
            })

    return alert_service.generate_alerts(risk_data)


@alert_router.post("/alerts/generate")
async def generate_alerts(request: Dict[str, Any], db: Session = Depends(get_db)):
    """Generate alerts with optional forecast and river data"""
    wards = db.query(Ward).all()
    risk_data = []

    for ward in wards:
        scores = db.query(WardRiskScore).filter(
            WardRiskScore.ward_id == ward.ward_id
        ).order_by(WardRiskScore.timestamp.desc()).first()

        if scores:
            risk_data.append({
                "ward_id": ward.ward_id,
                "ward_name": ward.name,
                "population": ward.population or 0,
                "elderly_ratio": ward.elderly_ratio or 8,
                "top_hazard": scores.top_hazard or "flood",
                "top_risk_score": scores.final_combined_risk or 0,
                "final_combined_risk": scores.final_combined_risk or 0,
            })

    return alert_service.generate_alerts(risk_data)


# ─── Feature: Evacuation Routing ─────────────────────────────────────────────
evacuation_route_router = APIRouter(prefix="/api", tags=["Evacuation"])


@evacuation_route_router.get("/shelters")
async def get_shelters():
    """List all shelter locations with capacity info"""
    return {
        "shelters": evacuation_router.get_shelters(),
        "total": len(evacuation_router.get_shelters()),
    }


@evacuation_route_router.get("/evacuation/{ward_id}")
async def get_evacuation_route(ward_id: str, db: Session = Depends(get_db)):
    """Get optimal evacuation route for a specific ward"""
    ward = db.query(Ward).filter(Ward.ward_id == ward_id).first()
    if not ward:
        raise HTTPException(status_code=404, detail=f"Ward {ward_id} not found")

    # Get current risk for this ward
    risk_score = db.query(WardRiskScore).filter(
        WardRiskScore.ward_id == ward_id
    ).order_by(WardRiskScore.timestamp.desc()).first()

    risk_data = None
    if risk_score:
        risk_data = {
            "top_risk_score": risk_score.final_combined_risk or 0,
            "final_combined_risk": risk_score.final_combined_risk or 0,
        }

    return evacuation_router.compute_evacuation_route(ward, risk_data)


@evacuation_route_router.get("/evacuation")
async def get_all_evacuation_routes(db: Session = Depends(get_db)):
    """Get evacuation routes for all wards"""
    wards = db.query(Ward).all()
    risk_map = {}

    for ward in wards:
        scores = db.query(WardRiskScore).filter(
            WardRiskScore.ward_id == ward.ward_id
        ).order_by(WardRiskScore.timestamp.desc()).first()
        if scores:
            risk_map[ward.ward_id] = {
                "top_risk_score": scores.final_combined_risk or 0,
                "final_combined_risk": scores.final_combined_risk or 0,
            }

    return evacuation_router.compute_all_routes(wards, risk_map)


# ─── Feature: Decision Support ───────────────────────────────────────────────
decision_router = APIRouter(prefix="/api", tags=["Decision Support"])


@decision_router.get("/decision-support")
async def get_decision_support(db: Session = Depends(get_db)):
    """Get full decision support action plan"""
    wards = db.query(Ward).all()

    # Gather risk data
    risk_data = []
    for ward in wards:
        scores = db.query(WardRiskScore).filter(
            WardRiskScore.ward_id == ward.ward_id
        ).order_by(WardRiskScore.timestamp.desc()).first()
        if scores:
            risk_data.append({
                "ward_id": ward.ward_id,
                "ward_name": ward.name,
                "population": ward.population or 0,
                "top_hazard": scores.top_hazard or "flood",
                "top_risk_score": scores.final_combined_risk or 0,
                "final_combined_risk": scores.final_combined_risk or 0,
            })

    # Try to get forecast data
    forecast_data = None
    try:
        weather_service = WeatherIngestionService()
        weather_result = await weather_service.ingest_for_wards(wards)
        weather_map = weather_result.get("wards", {})
        forecast_data = forecast_engine.compute_all_wards_forecast(wards, weather_map)
    except Exception as e:
        logger.warning(f"Forecast data unavailable for decision support: {e}")

    # Try to get river data
    river_data = None
    try:
        river_data = river_monitor.get_current_levels()
    except Exception as e:
        logger.warning(f"River data unavailable for decision support: {e}")

    return decision_support.generate_action_plan(
        risk_data, forecast_data, river_data
    )
