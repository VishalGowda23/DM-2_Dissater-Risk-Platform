"""
Core configuration for Disaster Intelligence Platform
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "Disaster Intelligence Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Database
    DATABASE_URL: str = "postgresql://disaster:disaster@localhost:5432/disaster_db"
    POSTGRES_USER: str = "disaster"
    POSTGRES_PASSWORD: str = "disaster"
    POSTGRES_DB: str = "disaster_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    CACHE_TTL: int = 600  # 10 minutes
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # Weather API (Open-Meteo is free and doesn't require API key)
    WEATHER_API_URL: str = "https://api.open-meteo.com/v1/forecast"
    WEATHER_API_KEY: Optional[str] = None
    WEATHER_CACHE_TTL: int = 600  # 10 minutes
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60
    
    # Pune City Configuration
    PUNE_CENTER_LAT: float = 18.5204
    PUNE_CENTER_LON: float = 73.8567
    PUNE_CITY_RADIUS_KM: float = 25
    
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
    
    # Risk Thresholds
    RISK_LOW_THRESHOLD: int = 30
    RISK_MODERATE_THRESHOLD: int = 60
    RISK_HIGH_THRESHOLD: int = 80
    RISK_CRITICAL_THRESHOLD: int = 100
    
    # Delta Thresholds
    DELTA_ESCALATION_THRESHOLD: float = 20.0
    DELTA_CRITICAL_THRESHOLD: float = 40.0
    
    # Resource Allocation
    MIN_ALLOCATION_CRITICAL_WARD: int = 1
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
