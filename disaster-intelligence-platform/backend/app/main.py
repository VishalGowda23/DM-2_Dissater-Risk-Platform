"""
PRAKALP - Production FastAPI Application
Main entry point with lifespan management, middleware, and API mounts
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("prakalp")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown"""
    from app.db.config import settings
    from app.db.database import init_db, check_postgis
    from app.db.cache import _is_redis_available
    from app.ml.model import ml_model
    from app.jobs.scheduler import start_scheduler, stop_scheduler

    logger.info("=" * 60)
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"   Environment: {settings.ENVIRONMENT}")
    logger.info("=" * 60)

    # Initialize database
    try:
        init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database init failed: {e}")

    # Check PostGIS
    if check_postgis():
        logger.info("✅ PostGIS enabled")
    else:
        logger.warning("⚠️ PostGIS not available (spatial queries will use fallback)")

    # Check Redis
    if _is_redis_available():
        logger.info("✅ Redis connected")
    else:
        logger.warning("⚠️ Redis not available (caching disabled)")

    # Load ML model
    if ml_model.load():
        logger.info("✅ ML model loaded")
    else:
        logger.info("⚠️ ML model not found (using fallback risk estimation)")

    # Initialize ward data
    try:
        from app.db.database import SessionLocal
        from app.services.ward_data_service import initialize_wards
        from app.services.auth import initialize_admin_user
        db = SessionLocal()
        result = initialize_wards(db)
        initialize_admin_user(db)
        db.close()
        logger.info(f"✅ Ward data: {result}")
    except Exception as e:
        logger.warning(f"⚠️ Ward initialization: {e}")

    # Start background scheduler
    try:
        start_scheduler()
        logger.info("✅ Background scheduler started")
    except Exception as e:
        logger.warning(f"⚠️ Scheduler failed: {e}")

    logger.info("=" * 60)
    logger.info("🟢 Platform ready")
    logger.info("=" * 60)

    yield

    # Shutdown
    logger.info("Shutting down...")
    stop_scheduler()


# Create FastAPI application
from app.db.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="PRAKALP — Predictive Risk Assessment And Knowledge Analytics For Localized Preparedness. "
                "Multi-hazard micro-level disaster intelligence for Pune with dual-layer risk assessment, "
                "real-time weather integration, scenario simulation, and resource optimization.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API routes
from app.api.routes import (
    health_router, ward_router, risk_router, compute_router,
    scenario_router, optimizer_router, auth_router, admin_router,
    forecast_router, historical_router, river_router, cascade_router,
    alert_router, evacuation_route_router, decision_router,
)

app.include_router(health_router)
app.include_router(ward_router)
app.include_router(risk_router)
app.include_router(compute_router)
app.include_router(scenario_router)
app.include_router(optimizer_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(forecast_router)
app.include_router(historical_router)
app.include_router(river_router)
app.include_router(cascade_router)
app.include_router(alert_router)
app.include_router(evacuation_route_router)
app.include_router(decision_router)

# Export for uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
    )
