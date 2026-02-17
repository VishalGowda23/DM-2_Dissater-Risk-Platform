"""
Database configuration with PostGIS support and SQLite fallback
Production: PostGIS with spatial queries
Local dev: SQLite with Python-based neighbor calculation
"""
from sqlalchemy import create_engine, text, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import logging
import math

from app.db.config import settings

logger = logging.getLogger(__name__)

# Detect database type
IS_SQLITE = settings.DATABASE_URL.startswith("sqlite")

# Create engine appropriate for database type
if IS_SQLITE:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=settings.DEBUG,
    )
else:
    from sqlalchemy.pool import QueuePool
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_recycle=settings.DB_POOL_RECYCLE,
        poolclass=QueuePool,
        echo=settings.DEBUG,
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables and PostGIS extension"""
    logger.info("Initializing database...")

    if not IS_SQLITE:
        # Create PostGIS extension for PostgreSQL
        with engine.connect() as conn:
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
                conn.commit()
                logger.info("PostGIS extension enabled")
            except Exception as e:
                logger.warning(f"Could not create PostGIS extension: {e}")

    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def check_postgis() -> bool:
    """Check if PostGIS extension is available"""
    if IS_SQLITE:
        return False
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT PostGIS_Version()"))
            version = result.scalar()
            logger.info(f"PostGIS version: {version}")
            return True
    except Exception as e:
        logger.debug(f"PostGIS not available: {e}")
        return False


def _haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate haversine distance between two points in km"""
    R = 6371  # Earth radius km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def get_ward_adjacency(db: Session, ward_id: str) -> list:
    """
    Get adjacent wards using PostGIS ST_Touches (or proximity fallback)
    Returns list of ward_ids that share a boundary with the given ward
    """
    if not IS_SQLITE:
        try:
            result = db.execute(text("""
                SELECT b.ward_id
                FROM wards a, wards b
                WHERE a.ward_id = :ward_id
                  AND a.ward_id != b.ward_id
                  AND a.geometry IS NOT NULL
                  AND b.geometry IS NOT NULL
                  AND ST_Touches(a.geometry, b.geometry)
            """), {"ward_id": ward_id})
            neighbors = [row[0] for row in result]
            if neighbors:
                return neighbors
        except Exception as e:
            logger.debug(f"ST_Touches failed for {ward_id}: {e}")

    # Fallback: use Python-based proximity
    return get_proximity_neighbors(db, ward_id)


def get_proximity_neighbors(db: Session, ward_id: str, radius_km: float = 3.0) -> list:
    """
    Fallback adjacency using centroid proximity (works with any DB)
    Returns wards within radius_km of the given ward's centroid
    """
    try:
        # Get all wards with centroids
        result = db.execute(text(
            "SELECT ward_id, centroid_lat, centroid_lon FROM wards WHERE centroid_lat IS NOT NULL"
        ))
        all_wards = [(row[0], row[1], row[2]) for row in result]

        # Find the target ward
        target = next((w for w in all_wards if w[0] == ward_id), None)
        if not target:
            return []

        # Calculate distances in Python
        neighbors = []
        for wid, lat, lon in all_wards:
            if wid == ward_id:
                continue
            dist = _haversine_distance(target[1], target[2], lat, lon)
            if dist < radius_km:
                neighbors.append(wid)

        return neighbors
    except Exception as e:
        logger.error(f"Proximity query failed for {ward_id}: {e}")
        return []
