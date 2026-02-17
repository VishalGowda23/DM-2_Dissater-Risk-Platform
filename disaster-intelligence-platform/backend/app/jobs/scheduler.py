"""
Background job scheduler using APScheduler
Runs weather ingestion (15 min), risk recomputation (30 min), cleanup (daily)
"""
import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from app.db.config import settings
from app.db.database import SessionLocal
from app.models.ward import Ward, WardRiskScore
from app.services.weather_service import WeatherIngestionService
from app.services.risk_engine.final_risk import final_risk_calculator
from app.db.cache import cache_risk_scores

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")


async def scheduled_weather_ingestion():
    """Fetch weather data for all wards"""
    logger.info("⏰ Scheduled weather ingestion starting...")
    db = SessionLocal()
    try:
        wards = db.query(Ward).all()
        service = WeatherIngestionService()
        result = await service.ingest_for_wards(wards)
        logger.info(f"Weather ingestion complete: {result.get('success', 0)} success, {result.get('failed', 0)} failed")
    except Exception as e:
        logger.error(f"Scheduled weather ingestion failed: {e}")
    finally:
        db.close()


async def scheduled_risk_recompute():
    """Recompute risk scores for all wards"""
    logger.info("⏰ Scheduled risk recomputation starting...")
    db = SessionLocal()
    try:
        wards = db.query(Ward).all()
        
        # Fetch weather first
        weather_service = WeatherIngestionService()
        weather_results = await weather_service.ingest_for_wards(wards)
        weather_data = weather_results.get("wards", {})

        processed = 0
        for ward in wards:
            try:
                ward_weather = weather_data.get(ward.ward_id)
                risk_data = final_risk_calculator.calculate_full_risk(
                    ward, wards, ward_weather, db
                )

                risk_score = WardRiskScore(
                    ward_id=ward.ward_id,
                    **{k: v for k, v in risk_data.items() if hasattr(WardRiskScore, k)}
                )
                db.add(risk_score)
                cache_risk_scores(ward.ward_id, risk_data)
                processed += 1
            except Exception as e:
                logger.error(f"Risk recompute failed for {ward.ward_id}: {e}")

        db.commit()
        logger.info(f"Risk recomputation complete: {processed} wards processed")

    except Exception as e:
        logger.error(f"Scheduled risk recompute failed: {e}")
        db.rollback()
    finally:
        db.close()


async def scheduled_cleanup():
    """Clean up risk scores older than 30 days"""
    logger.info("⏰ Scheduled data cleanup starting...")
    db = SessionLocal()
    try:
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=30)
        deleted = db.query(WardRiskScore).filter(
            WardRiskScore.timestamp < cutoff
        ).delete()
        db.commit()
        logger.info(f"Cleaned up {deleted} old risk score records")
    except Exception as e:
        logger.error(f"Data cleanup failed: {e}")
        db.rollback()
    finally:
        db.close()


def start_scheduler():
    """Start background job scheduler"""
    scheduler.add_job(
        scheduled_weather_ingestion,
        trigger=IntervalTrigger(minutes=settings.WEATHER_INGEST_INTERVAL_MIN),
        id="weather_ingestion",
        name="Weather Data Ingestion",
        replace_existing=True,
    )

    scheduler.add_job(
        scheduled_risk_recompute,
        trigger=IntervalTrigger(minutes=settings.RISK_RECOMPUTE_INTERVAL_MIN),
        id="risk_recompute",
        name="Risk Score Recomputation",
        replace_existing=True,
    )

    scheduler.add_job(
        scheduled_cleanup,
        trigger=CronTrigger(hour=settings.DATA_CLEANUP_HOUR, minute=0),
        id="data_cleanup",
        name="Old Data Cleanup",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        f"📅 Background scheduler started: "
        f"weather every {settings.WEATHER_INGEST_INTERVAL_MIN}min, "
        f"risk every {settings.RISK_RECOMPUTE_INTERVAL_MIN}min, "
        f"cleanup at {settings.DATA_CLEANUP_HOUR}:00"
    )


def stop_scheduler():
    """Stop background scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Background scheduler stopped")
