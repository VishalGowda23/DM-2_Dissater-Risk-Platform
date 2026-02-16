"""
Database configuration and session management
"""
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from geoalchemy2 import Geometry
import logging

from core.config import settings

logger = logging.getLogger(__name__)

# Create engine with proper configuration for PostGIS
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.DEBUG,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Session:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def check_postgis():
    """Check if PostGIS extension is available"""
    db = SessionLocal()
    try:
        result = db.execute("SELECT PostGIS_Version();")
        version = result.scalar()
        logger.info(f"PostGIS version: {version}")
        return True
    except Exception as e:
        logger.error(f"PostGIS not available: {e}")
        return False
    finally:
        db.close()
