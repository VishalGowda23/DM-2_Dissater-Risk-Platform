"""
Ward model with geospatial data for Pune Municipal Corporation
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Index
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from shapely.geometry import mapping, shape
from shapely.wkb import loads as wkb_loads
import logging

from core.database import Base

logger = logging.getLogger(__name__)


class Ward(Base):
    """Ward model representing Pune Municipal Corporation wards"""
    __tablename__ = "wards"
    
    id = Column(Integer, primary_key=True, index=True)
    ward_id = Column(String(10), unique=True, nullable=False, index=True)
    ward_name = Column(String(100), nullable=False)
    ward_name_marathi = Column(String(100), nullable=True)
    
    # Geospatial data
    centroid_lat = Column(Float, nullable=False)
    centroid_lon = Column(Float, nullable=False)
    geometry = Column(Geometry('POLYGON', srid=4326), nullable=True)
    
    # Demographics
    population = Column(Integer, nullable=False, default=0)
    population_density = Column(Float, nullable=True)  # per sq km
    elderly_population = Column(Integer, nullable=True)  # 60+ years
    elderly_ratio = Column(Float, nullable=True)  # percentage
    
    # Physical characteristics
    area_sqkm = Column(Float, nullable=True)
    mean_elevation_m = Column(Float, nullable=True)
    min_elevation_m = Column(Float, nullable=True)
    max_elevation_m = Column(Float, nullable=True)
    slope_mean = Column(Float, nullable=True)  # average slope in degrees
    
    # Infrastructure proxies
    drainage_index = Column(Float, nullable=True)  # 0-1, higher is better drainage
    impervious_surface_pct = Column(Float, nullable=True)  # percentage
    building_density = Column(Float, nullable=True)  # buildings per sq km
    
    # Historical data
    historical_flood_count_10y = Column(Integer, default=0)
    historical_heatwave_days_10y = Column(Integer, default=0)
    last_major_flood_year = Column(Integer, nullable=True)
    
    # Risk scores (cached)
    baseline_flood_risk = Column(Float, nullable=True)
    baseline_heat_risk = Column(Float, nullable=True)
    
    # Metadata
    data_sources = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_ward_centroid', 'centroid_lat', 'centroid_lon'),
        Index('idx_ward_population', 'population'),
        Index('idx_ward_geometry', 'geometry', postgresql_using='gist'),
    )
    
    def get_centroid(self) -> tuple:
        """Get ward centroid as (lat, lon) tuple"""
        return (self.centroid_lat, self.centroid_lon)
    
    def get_geometry_geojson(self) -> dict:
        """Get ward geometry as GeoJSON"""
        if self.geometry is None:
            return None
        try:
            geom = wkb_loads(self.geometry)
            return mapping(geom)
        except Exception as e:
            logger.error(f"Error converting geometry for ward {self.ward_id}: {e}")
            return None
    
    def to_dict(self, include_geometry: bool = False) -> dict:
        """Convert ward to dictionary"""
        data = {
            "id": self.id,
            "ward_id": self.ward_id,
            "ward_name": self.ward_name,
            "ward_name_marathi": self.ward_name_marathi,
            "centroid": {
                "lat": self.centroid_lat,
                "lon": self.centroid_lon
            },
            "population": self.population,
            "population_density": self.population_density,
            "elderly_ratio": self.elderly_ratio,
            "area_sqkm": self.area_sqkm,
            "elevation_m": self.mean_elevation_m,
            "drainage_index": self.drainage_index,
            "impervious_surface_pct": self.impervious_surface_pct,
            "historical_flood_count_10y": self.historical_flood_count_10y,
            "historical_heatwave_days_10y": self.historical_heatwave_days_10y,
            "baseline_flood_risk": self.baseline_flood_risk,
            "baseline_heat_risk": self.baseline_heat_risk,
        }
        
        if include_geometry:
            data["geometry"] = self.get_geometry_geojson()
        
        return data
    
    def calculate_vulnerability_score(self) -> float:
        """Calculate baseline vulnerability score (0-1)"""
        scores = []
        
        # Elevation vulnerability (lower elevation = higher vulnerability)
        if self.mean_elevation_m is not None:
            # Normalize: Pune elevation ranges from 500-800m
            elevation_score = max(0, min(1, (650 - self.mean_elevation_m) / 150))
            scores.append(elevation_score)
        
        # Drainage weakness (lower index = higher vulnerability)
        if self.drainage_index is not None:
            drainage_score = 1 - self.drainage_index
            scores.append(drainage_score)
        
        # Population density (higher density = higher vulnerability)
        if self.population_density is not None:
            density_score = min(1, self.population_density / 20000)  # Normalize to 20k/sqkm
            scores.append(density_score)
        
        return sum(scores) / len(scores) if scores else 0.5


class WardRiskScore(Base):
    """Real-time risk scores for wards"""
    __tablename__ = "ward_risk_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    ward_id = Column(String(10), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Flood risk
    flood_baseline_risk = Column(Float, nullable=True)  # 0-100
    flood_event_risk = Column(Float, nullable=True)  # 0-100
    flood_risk_delta = Column(Float, nullable=True)  # event - baseline
    flood_risk_delta_pct = Column(Float, nullable=True)  # percentage change
    
    # Heat risk
    heat_baseline_risk = Column(Float, nullable=True)  # 0-100
    heat_event_risk = Column(Float, nullable=True)  # 0-100
    heat_risk_delta = Column(Float, nullable=True)
    heat_risk_delta_pct = Column(Float, nullable=True)
    
    # Current hazard values
    current_rainfall_mm = Column(Float, nullable=True)
    rainfall_forecast_48h_mm = Column(Float, nullable=True)
    current_temp_c = Column(Float, nullable=True)
    temp_anomaly_c = Column(Float, nullable=True)
    
    # Risk factors breakdown
    risk_factors = Column(JSON, default=dict)  # Detailed factor contributions
    
    # Top threat
    top_hazard = Column(String(20), nullable=True)  # 'flood', 'heat', 'none'
    top_risk_score = Column(Float, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_risk_ward_time', 'ward_id', 'timestamp'),
        Index('idx_risk_flood', 'flood_event_risk'),
        Index('idx_risk_heat', 'heat_event_risk'),
    )
    
    def to_dict(self) -> dict:
        """Convert risk score to dictionary"""
        return {
            "ward_id": self.ward_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "flood": {
                "baseline": round(self.flood_baseline_risk, 1) if self.flood_baseline_risk else None,
                "event": round(self.flood_event_risk, 1) if self.flood_event_risk else None,
                "delta": round(self.flood_risk_delta, 1) if self.flood_risk_delta else None,
                "delta_pct": round(self.flood_risk_delta_pct, 1) if self.flood_risk_delta_pct else None,
            },
            "heat": {
                "baseline": round(self.heat_baseline_risk, 1) if self.heat_baseline_risk else None,
                "event": round(self.heat_event_risk, 1) if self.heat_event_risk else None,
                "delta": round(self.heat_risk_delta, 1) if self.heat_risk_delta else None,
                "delta_pct": round(self.heat_risk_delta_pct, 1) if self.heat_risk_delta_pct else None,
            },
            "current_conditions": {
                "rainfall_mm": self.current_rainfall_mm,
                "rainfall_forecast_48h_mm": self.rainfall_forecast_48h_mm,
                "temperature_c": self.current_temp_c,
                "temp_anomaly_c": self.temp_anomaly_c,
            },
            "top_hazard": self.top_hazard,
            "top_risk_score": round(self.top_risk_score, 1) if self.top_risk_score else None,
            "risk_factors": self.risk_factors,
        }
