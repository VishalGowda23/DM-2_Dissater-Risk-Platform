"""
Celery tasks for background data ingestion and processing
"""
from celery import shared_task
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from core.database import SessionLocal
from core.celery import celery_app
from ingestion.weather_api import WeatherIngestionService
from ingestion.init_data import initialize_all_data
from risk_engine.baseline import BaselineRiskCalculator
from risk_engine.event_risk import EventRiskCalculator
from models.ward import Ward, WardRiskScore

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def ingest_weather_data(self):
    """Task to ingest weather data for all wards"""
    logger.info("Starting scheduled weather data ingestion")
    
    db = SessionLocal()
    service = WeatherIngestionService()
    
    try:
        wards = db.query(Ward).all()
        result = service.ingest_for_wards(wards)
        
        logger.info(f"Weather ingestion complete: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"Weather ingestion failed: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    finally:
        db.close()


@shared_task(bind=True, max_retries=3)
def calculate_risk_scores(self):
    """Task to calculate risk scores for all wards"""
    logger.info("Starting scheduled risk score calculation")
    
    db = SessionLocal()
    baseline_calc = BaselineRiskCalculator()
    event_calc = EventRiskCalculator()
    
    try:
        wards = db.query(Ward).all()
        
        processed = 0
        failed = 0
        
        for ward in wards:
            try:
                # Calculate baselines
                flood_baseline = baseline_calc.calculate_flood_baseline(ward, wards)
                heat_baseline = baseline_calc.calculate_heatwave_baseline(ward, wards)
                
                # Calculate event risks
                flood_event_result = event_calc.calculate_flood_event_risk(
                    ward, 
                    baseline_vulnerability=flood_baseline / 100
                )
                heat_event_result = event_calc.calculate_heat_event_risk(
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
                processed += 1
                
            except Exception as e:
                logger.error(f"Error calculating risk for ward {ward.ward_id}: {e}")
                failed += 1
        
        db.commit()
        
        result = {
            "processed": processed,
            "failed": failed,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Risk calculation complete: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"Risk calculation failed: {exc}")
        db.rollback()
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    finally:
        db.close()


@shared_task
def cleanup_old_data():
    """Task to clean up old data (runs daily)"""
    logger.info("Starting data cleanup")
    
    db = SessionLocal()
    
    try:
        # Delete risk scores older than 30 days
        cutoff_date = datetime.now() - timedelta(days=30)
        
        deleted = db.query(WardRiskScore).filter(
            WardRiskScore.timestamp < cutoff_date
        ).delete()
        
        db.commit()
        
        logger.info(f"Cleaned up {deleted} old risk score records")
        return {"deleted_records": deleted}
        
    except Exception as e:
        logger.error(f"Data cleanup failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@shared_task
def initialize_database():
    """Task to initialize database with seed data"""
    logger.info("Starting database initialization")
    
    try:
        result = initialize_all_data()
        logger.info(f"Database initialization complete: {result}")
        return result
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
