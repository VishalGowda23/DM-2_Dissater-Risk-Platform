"""
Core configuration for Disaster Intelligence Platform
Production-grade settings with environment variable loading
"""
from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "Disaster Intelligence Platform"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # Database (PostGIS recommended, SQLite fallback for local dev)
    DATABASE_URL: str = "sqlite:///./disaster_local.db"
    POSTGRES_USER: str = "disaster"
    POSTGRES_PASSWORD: str = "disaster"
    POSTGRES_DB: str = "disaster_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 300

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    CACHE_TTL: int = 900  # 15 minutes
    WEATHER_CACHE_TTL: int = 900  # 15 minutes

    # JWT Authentication
    SECRET_KEY: str = "your-secret-key-change-in-production-must-be-at-least-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000", "http://localhost:8080"]

    # Weather API (Open-Meteo - free, no API key)
    WEATHER_API_URL: str = "https://api.open-meteo.com/v1/forecast"
    WEATHER_ARCHIVE_URL: str = "https://archive-api.open-meteo.com/v1/archive"
    WEATHER_FORECAST_DAYS: int = 7

    # OSM Overpass API
    OVERPASS_API_URL: str = "https://overpass-api.de/api/interpreter"
    OSM_CACHE_TTL: int = 86400  # 24 hours

    # DEM Processing
    SRTM_DATA_DIR: str = "./data/srtm"
    DEM_RESOLUTION: int = 30  # meters

    # Pune City Configuration
    PUNE_CENTER_LAT: float = 18.5204
    PUNE_CENTER_LON: float = 73.8567
    PUNE_CITY_RADIUS_KM: float = 25
    PUNE_BBOX: dict = {
        "min_lat": 18.40, "max_lat": 18.65,
        "min_lon": 73.73, "max_lon": 73.97
    }

    # Risk Model Weights
    FLOOD_BASELINE_WEIGHTS: dict = {
        "historical_frequency": 0.50,
        "elevation_vulnerability": 0.30,
        "drainage_weakness": 0.20
    }
    FLOOD_EVENT_WEIGHTS: dict = {
        "forecast_rainfall_intensity": 0.60,
        "cumulative_rain_48h": 0.20,
        "baseline_vulnerability": 0.20
    }
    HEAT_EVENT_WEIGHTS: dict = {
        "temperature_anomaly": 0.70,
        "baseline_vulnerability": 0.30
    }

    # ML Calibration
    ML_COMPOSITE_WEIGHT: float = 0.60
    ML_MODEL_WEIGHT: float = 0.40
    ML_MODEL_PATH: str = "./app/ml/data/model.pkl"

    # Risk Thresholds
    RISK_LOW_THRESHOLD: int = 30
    RISK_MODERATE_THRESHOLD: int = 60
    RISK_HIGH_THRESHOLD: int = 80
    RISK_CRITICAL_THRESHOLD: int = 100

    # Delta Thresholds
    DELTA_SURGE_THRESHOLD: float = 20.0
    DELTA_CRITICAL_THRESHOLD: float = 40.0

    # Neighbor Spillover
    NEIGHBOR_SPILLOVER_PCT: float = 5.0
    NEIGHBOR_RISK_THRESHOLD: float = 80.0

    # Resource Allocation
    MIN_ALLOCATION_CRITICAL_WARD: int = 1

    # Background Jobs
    WEATHER_INGEST_INTERVAL_MIN: int = 15
    RISK_RECOMPUTE_INTERVAL_MIN: int = 30
    DATA_CLEANUP_HOUR: int = 2

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
