"""
PRAKALP - Main FastAPI Application
"""
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import logging
import time
from datetime import datetime
from typing import List, Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import core components
from core.config import settings
from core.database import get_db, init_db, check_postgis
from core.cache import redis_client

# Import models
from models.ward import Ward, WardRiskScore
from models.historical_event import HistoricalEvent
from models.resource import ResourceInventory

# Import risk engine
from risk_engine.baseline import BaselineRiskCalculator
from risk_engine.event_risk import EventRiskCalculator
from risk_engine.explainability import explainer
from risk_engine.scenario import scenario_engine, ScenarioParameters

# Import optimizer
from optimizer.resource_allocator import allocator

# Import ingestion
from ingestion.weather_api import WeatherAPIClient, WeatherIngestionService

# Setup FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting up PRAKALP...")
    
    # Initialize database
    init_db()
    check_postgis()
    
    # Test Redis connection
    try:
        redis_client.ping()
        logger.info("Redis connection successful")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
    
    yield
    
    logger.info("Shutting down PRAKALP...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="PRAKALP — Predictive Risk Assessment And Knowledge Analytics For Localized Preparedness",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# Initialize components
baseline_calc = BaselineRiskCalculator()
event_calc = EventRiskCalculator()
weather_service = WeatherIngestionService()


# Helper functions
async def get_current_ward_risks(db: Session) -> List[Dict]:
    """Get current risk scores for all wards"""
    wards = db.query(Ward).all()
    
    # Get latest risk scores
    latest_scores = {}
    for ward in wards:
        score = db.query(WardRiskScore).filter(
            WardRiskScore.ward_id == ward.ward_id
        ).order_by(WardRiskScore.timestamp.desc()).first()
        
        if score:
            latest_scores[ward.ward_id] = score
    
    return wards, latest_scores


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {}
    }
    
    # Check database
    try:
        db = next(get_db())
        db.execute("SELECT 1")
        health["services"]["database"] = "healthy"
    except Exception as e:
        health["services"]["database"] = f"unhealthy: {str(e)}"
        health["status"] = "degraded"
    
    # Check Redis
    try:
        redis_client.ping()
        health["services"]["redis"] = "healthy"
    except Exception as e:
        health["services"]["redis"] = f"unhealthy: {str(e)}"
    
    return health


@app.get("/api/wards")
async def get_wards(
    include_geometry: bool = Query(False, description="Include ward geometry"),
    db: Session = Depends(get_db)
):
    """Get all wards with their data"""
    wards = db.query(Ward).all()
    return {
        "count": len(wards),
        "wards": [ward.to_dict(include_geometry=include_geometry) for ward in wards]
    }


@app.get("/api/wards/{ward_id}")
async def get_ward(
    ward_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed information for a specific ward"""
    ward = db.query(Ward).filter(Ward.ward_id == ward_id).first()
    
    if not ward:
        raise HTTPException(status_code=404, detail=f"Ward {ward_id} not found")
    
    # Get latest risk score
    risk_score = db.query(WardRiskScore).filter(
        WardRiskScore.ward_id == ward_id
    ).order_by(WardRiskScore.timestamp.desc()).first()
    
    return {
        "ward": ward.to_dict(include_geometry=True),
        "current_risk": risk_score.to_dict() if risk_score else None
    }


@app.get("/api/risk")
async def get_risk(
    hazard: Optional[str] = Query(None, description="Filter by hazard: flood, heat"),
    ward_id: Optional[str] = Query(None, description="Filter by ward"),
    db: Session = Depends(get_db)
):
    """
    Get current risk scores
    
    - hazard: Filter by specific hazard (flood, heat)
    - ward_id: Filter by specific ward
    """
    wards = db.query(Ward).all()
    
    if ward_id:
        wards = [w for w in wards if w.ward_id == ward_id]
        if not wards:
            raise HTTPException(status_code=404, detail=f"Ward {ward_id} not found")
    
    risk_data = []
    
    for ward in wards:
        # Get latest risk score
        score = db.query(WardRiskScore).filter(
            WardRiskScore.ward_id == ward.ward_id
        ).order_by(WardRiskScore.timestamp.desc()).first()
        
        if score:
            risk_entry = {
                "ward_id": ward.ward_id,
                "ward_name": ward.ward_name,
                "population": ward.population,
                "centroid": {"lat": ward.centroid_lat, "lon": ward.centroid_lon}
            }
            
            if hazard == "flood" or hazard is None:
                risk_entry["flood"] = {
                    "baseline": score.flood_baseline_risk,
                    "event": score.flood_event_risk,
                    "delta": score.flood_risk_delta,
                    "delta_pct": score.flood_risk_delta_pct
                }
            
            if hazard == "heat" or hazard is None:
                risk_entry["heat"] = {
                    "baseline": score.heat_baseline_risk,
                    "event": score.heat_event_risk,
                    "delta": score.heat_risk_delta,
                    "delta_pct": score.heat_risk_delta_pct
                }
            
            risk_entry["top_hazard"] = score.top_hazard
            risk_entry["top_risk_score"] = score.top_risk_score
            
            risk_data.append(risk_entry)
    
    # Sort by risk score (descending)
    risk_data.sort(key=lambda x: x.get("top_risk_score", 0), reverse=True)
    
    return {
        "timestamp": datetime.now().isoformat(),
        "count": len(risk_data),
        "risk_data": risk_data
    }


@app.get("/api/risk/summary")
async def get_risk_summary(db: Session = Depends(get_db)):
    """Get aggregate risk summary for the city"""
    wards = db.query(Ward).all()
    
    total_population = sum(w.population for w in wards)
    
    # Get latest risk scores
    risk_scores = []
    critical_wards = []
    high_wards = []
    
    for ward in wards:
        score = db.query(WardRiskScore).filter(
            WardRiskScore.ward_id == ward.ward_id
        ).order_by(WardRiskScore.timestamp.desc()).first()
        
        if score:
            risk_scores.append(score)
            
            if score.flood_event_risk and score.flood_event_risk > 80:
                critical_wards.append({"ward_id": ward.ward_id, "hazard": "flood", "risk": score.flood_event_risk})
            if score.heat_event_risk and score.heat_event_risk > 80:
                critical_wards.append({"ward_id": ward.ward_id, "hazard": "heat", "risk": score.heat_event_risk})
            
            if score.flood_event_risk and 60 < score.flood_event_risk <= 80:
                high_wards.append({"ward_id": ward.ward_id, "hazard": "flood", "risk": score.flood_event_risk})
            if score.heat_event_risk and 60 < score.heat_event_risk <= 80:
                high_wards.append({"ward_id": ward.ward_id, "hazard": "heat", "risk": score.heat_event_risk})
    
    avg_flood_risk = sum(s.flood_event_risk for s in risk_scores if s.flood_event_risk) / len(risk_scores) if risk_scores else 0
    avg_heat_risk = sum(s.heat_event_risk for s in risk_scores if s.heat_event_risk) / len(risk_scores) if risk_scores else 0
    
    return {
        "timestamp": datetime.now().isoformat(),
        "city": "Pune",
        "total_wards": len(wards),
        "total_population": total_population,
        "average_risks": {
            "flood": round(avg_flood_risk, 1),
            "heat": round(avg_heat_risk, 1)
        },
        "critical_wards": {
            "count": len(critical_wards),
            "wards": critical_wards[:5]  # Top 5
        },
        "high_risk_wards": {
            "count": len(high_wards),
            "wards": high_wards[:5]
        },
        "overall_status": "critical" if critical_wards else "high" if high_wards else "normal"
    }


@app.get("/api/explain/{ward_id}")
async def explain_ward_risk(
    ward_id: str,
    hazard: str = Query("flood", description="Hazard type: flood, heat"),
    db: Session = Depends(get_db)
):
    """Get detailed explanation for a ward's risk score"""
    ward = db.query(Ward).filter(Ward.ward_id == ward_id).first()
    
    if not ward:
        raise HTTPException(status_code=404, detail=f"Ward {ward_id} not found")
    
    # Get latest risk score
    score = db.query(WardRiskScore).filter(
        WardRiskScore.ward_id == ward_id
    ).order_by(WardRiskScore.timestamp.desc()).first()
    
    if not score:
        raise HTTPException(status_code=404, detail=f"No risk data available for ward {ward_id}")
    
    # Get risk factors
    risk_factors = score.risk_factors or {}
    
    ward_data = ward.to_dict()
    
    if hazard == "flood":
        explanation = explainer.explain_flood_risk(
            baseline_risk=score.flood_baseline_risk or 0,
            event_risk=score.flood_event_risk or 0,
            baseline_factors=risk_factors.get("flood_baseline", {}),
            event_factors=risk_factors.get("flood_event", {}),
            ward_data=ward_data
        )
    elif hazard == "heat":
        explanation = explainer.explain_heat_risk(
            baseline_risk=score.heat_baseline_risk or 0,
            event_risk=score.heat_event_risk or 0,
            baseline_factors=risk_factors.get("heat_baseline", {}),
            event_factors=risk_factors.get("heat_event", {}),
            ward_data=ward_data
        )
    else:
        raise HTTPException(status_code=400, detail=f"Invalid hazard type: {hazard}")
    
    return explanation


@app.post("/api/optimize")
async def optimize_resources(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Optimize resource allocation
    
    Request body:
    {
        "resources": {
            "pumps": 10,
            "buses": 5,
            "relief_camps": 3,
            "cooling_centers": 4,
            "medical_units": 2
        },
        "scenario": {
            "use_delta": false
        }
    }
    """
    resources = request.get("resources", {})
    scenario = request.get("scenario", {})
    
    # Get current ward risks
    wards = db.query(Ward).all()
    
    ward_data = []
    for ward in wards:
        score = db.query(WardRiskScore).filter(
            WardRiskScore.ward_id == ward.ward_id
        ).order_by(WardRiskScore.timestamp.desc()).first()
        
        if score:
            ward_data.append({
                "ward_id": ward.ward_id,
                "ward_name": ward.ward_name,
                "population": ward.population,
                "flood_risk": score.flood_event_risk or 0,
                "heat_risk": score.heat_event_risk or 0,
                "risk_delta": max(
                    score.flood_risk_delta or 0,
                    score.heat_risk_delta or 0
                )
            })
    
    # Run optimization
    result = allocator.optimize_allocation(ward_data, resources, scenario)
    
    return result


@app.get("/api/scenarios")
async def get_scenarios():
    """Get available scenario presets"""
    return {
        "scenarios": scenario_engine.get_available_scenarios()
    }


@app.post("/api/scenario")
async def run_scenario(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Run a scenario simulation
    
    Request body:
    {
        "scenario_key": "heavy_rain",
        "custom_params": {
            "rainfall_multiplier": 1.5,
            "temp_anomaly_addition": 0
        }
    }
    """
    scenario_key = request.get("scenario_key", "default")
    custom_params = request.get("custom_params", {})
    
    # Get current ward risks
    wards = db.query(Ward).all()
    
    ward_data = []
    for ward in wards:
        score = db.query(WardRiskScore).filter(
            WardRiskScore.ward_id == ward.ward_id
        ).order_by(WardRiskScore.timestamp.desc()).first()
        
        if score:
            ward_data.append({
                "ward_id": ward.ward_id,
                "ward_name": ward.ward_name,
                "population": ward.population,
                "flood_baseline_risk": score.flood_baseline_risk,
                "flood_event_risk": score.flood_event_risk,
                "heat_baseline_risk": score.heat_baseline_risk,
                "heat_event_risk": score.heat_event_risk,
                "top_hazard": score.top_hazard,
                "top_risk_score": score.top_risk_score
            })
    
    # Run scenario
    if custom_params:
        scenario = ScenarioParameters(
            name="Custom Scenario",
            **custom_params
        )
        results = []
        for ward in ward_data:
            modified = scenario_engine.apply_scenario(ward, scenario)
            results.append({
                "baseline": ward,
                "scenario": modified
            })
        
        return {
            "scenario": scenario.to_dict(),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    else:
        return scenario_engine.run_scenario_comparison(ward_data, scenario_key)


@app.post("/api/ingest/weather")
async def ingest_weather(db: Session = Depends(get_db)):
    """Trigger weather data ingestion for all wards"""
    try:
        wards = db.query(Ward).all()
        result = await weather_service.ingest_for_wards(wards)
        return result
    except Exception as e:
        logger.error(f"Weather ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.post("/api/calculate-risks")
async def calculate_all_risks(db: Session = Depends(get_db)):
    """Trigger risk calculation for all wards"""
    try:
        wards = db.query(Ward).all()
        
        results = {
            "processed": 0,
            "failed": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        for ward in wards:
            try:
                # Calculate baselines
                flood_baseline = baseline_calc.calculate_flood_baseline(ward, wards)
                heat_baseline = baseline_calc.calculate_heatwave_baseline(ward, wards)
                
                # Update ward
                ward.baseline_flood_risk = flood_baseline
                ward.baseline_heat_risk = heat_baseline
                
                # Calculate event risks
                flood_event_result = await event_calc.calculate_flood_event_risk(
                    ward, 
                    baseline_vulnerability=flood_baseline / 100
                )
                heat_event_result = await event_calc.calculate_heat_event_risk(
                    ward,
                    baseline_vulnerability=heat_baseline / 100
                )
                
                flood_event = flood_event_result["event_risk"]
                heat_event = heat_event_result["event_risk"]
                
                # Calculate deltas
                flood_delta = event_calc.calculate_risk_delta(flood_event, flood_baseline)
                heat_delta = event_calc.calculate_risk_delta(heat_event, heat_baseline)
                
                # Determine top hazard
                if flood_event > heat_event and flood_event > 30:
                    top_hazard = "flood"
                    top_risk = flood_event
                elif heat_event > flood_event and heat_event > 30:
                    top_hazard = "heat"
                    top_risk = heat_event
                else:
                    top_hazard = "none"
                    top_risk = max(flood_event, heat_event)
                
                # Create risk score record
                risk_score = WardRiskScore(
                    ward_id=ward.ward_id,
                    flood_baseline_risk=flood_baseline,
                    flood_event_risk=flood_event,
                    flood_risk_delta=flood_delta["delta"],
                    flood_risk_delta_pct=flood_delta["delta_pct"],
                    heat_baseline_risk=heat_baseline,
                    heat_event_risk=heat_event,
                    heat_risk_delta=heat_delta["delta"],
                    heat_risk_delta_pct=heat_delta["delta_pct"],
                    current_rainfall_mm=flood_event_result.get("current_rainfall_mm"),
                    rainfall_forecast_48h_mm=flood_event_result.get("rainfall_forecast_48h_mm"),
                    current_temp_c=heat_event_result.get("current_temp_c"),
                    temp_anomaly_c=heat_event_result.get("temp_anomaly_c"),
                    risk_factors={
                        "flood_event": flood_event_result.get("factors", {}),
                        "heat_event": heat_event_result.get("factors", {})
                    },
                    top_hazard=top_hazard,
                    top_risk_score=top_risk
                )
                
                db.add(risk_score)
                results["processed"] += 1
                
            except Exception as e:
                logger.error(f"Error calculating risk for ward {ward.ward_id}: {e}")
                results["failed"] += 1
        
        db.commit()
        return results
        
    except Exception as e:
        logger.error(f"Risk calculation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Calculation failed: {str(e)}")


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "timestamp": datetime.now().isoformat()}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
