"""
Ward and WardRiskScore models with PostGIS geometry support
Production-grade with real GeoJSON polygon storage
"""
from sqlalchemy import (
    Column, Integer, Float, String, Text, Boolean, DateTime, JSON,
    ForeignKey, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime
import json

# GeoAlchemy2 is optional — SQLite works without it
try:
    from geoalchemy2 import Geometry
    HAS_GEO = True
except ImportError:
    HAS_GEO = False
    Geometry = None

from app.db.database import Base


class Ward(Base):
    """
    Ward model storing real Pune municipal ward data with PostGIS geometries
    """
    __tablename__ = "wards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ward_id = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    zone = Column(String(50))

    # PostGIS geometry (polygon boundary) - optional, falls back to Text for SQLite
    if HAS_GEO:
        geometry = Column(Geometry("MULTIPOLYGON", srid=4326), nullable=True)
    else:
        geometry = Column(Text, nullable=True)  # store GeoJSON as text fallback
    centroid_lat = Column(Float, nullable=False)
    centroid_lon = Column(Float, nullable=False)
    area_sq_km = Column(Float)

    # Demographics (Real Census/WorldPop data)
    population = Column(Integer, default=0)
    population_density = Column(Float, default=0.0)  # per sq km
    elderly_ratio = Column(Float, default=0.10)  # fraction 0-1
    settlement_pct = Column(Float, default=0.5)  # fraction of built-up area

    # Physical Characteristics (from DEM processing)
    elevation_m = Column(Float)
    mean_slope = Column(Float)  # degrees
    min_elevation_m = Column(Float)
    max_elevation_m = Column(Float)
    low_lying_index = Column(Float, default=0.5)  # 0-1 higher = more low-lying

    # Infrastructure (from OSM Overpass)
    drainage_index = Column(Float, default=0.5)  # 0-1, higher = better drainage
    impervious_surface_pct = Column(Float)
    hospital_count = Column(Integer, default=0)
    fire_station_count = Column(Integer, default=0)
    shelter_count = Column(Integer, default=0)
    school_count = Column(Integer, default=0)
    road_density_km = Column(Float, default=0.0)  # km of road per sq km
    infrastructure_density = Column(Float, default=0.0)  # aggregate score

    # Historical Disaster Data (real records)
    historical_flood_events = Column(Integer, default=0)
    historical_flood_frequency = Column(Float, default=0.0)  # events per year
    avg_annual_rainfall_mm = Column(Float, default=750.0)
    historical_heatwave_days = Column(Integer, default=0)

    # Seasonal Baselines (real historical averages)
    baseline_avg_rainfall_mm = Column(Float, default=750.0)
    baseline_avg_temp_c = Column(Float, default=28.0)

    # Data Quality
    data_completeness = Column(Float, default=0.5)  # 0-1, fraction of fields populated
    last_dem_update = Column(DateTime)
    last_osm_update = Column(DateTime)
    last_census_update = Column(DateTime)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    risk_scores = relationship("WardRiskScore", back_populates="ward", order_by="desc(WardRiskScore.timestamp)")

    # Indexes for spatial queries
    __table_args__ = (
        Index("idx_ward_centroid", "centroid_lat", "centroid_lon"),
        Index("idx_ward_population", "population"),
    )

    def to_dict(self, include_geometry: bool = False) -> dict:
        """Convert to dictionary for API response"""
        result = {
            "ward_id": self.ward_id,
            "name": self.name,
            "ward_name": self.name,  # frontend expects ward_name
            "zone": self.zone,
            "centroid": {"lat": self.centroid_lat, "lon": self.centroid_lon},
            "area_sq_km": self.area_sq_km,
            "population": self.population,
            "population_density": self.population_density,
            "elderly_ratio": self.elderly_ratio,
            "settlement_pct": self.settlement_pct,
            "elevation_m": self.elevation_m,
            "mean_slope": self.mean_slope,
            "low_lying_index": self.low_lying_index,
            "drainage_index": self.drainage_index,
            "hospital_count": self.hospital_count,
            "fire_station_count": self.fire_station_count,
            "shelter_count": self.shelter_count,
            "road_density_km": self.road_density_km,
            "infrastructure_density": self.infrastructure_density,
            "historical_flood_events": self.historical_flood_events,
            "historical_flood_frequency": self.historical_flood_frequency,
            "historical_heatwave_days": self.historical_heatwave_days,
            "data_completeness": self.data_completeness,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        return result

    def calculate_vulnerability_score(self) -> float:
        """Calculate overall vulnerability score (0-1)"""
        factors = []

        # Elevation vulnerability (lower = more vulnerable)
        if self.elevation_m and self.elevation_m > 0:
            elev_vuln = max(0, min(1, 1 - (self.elevation_m - 500) / 200))
            factors.append(elev_vuln * 0.25)

        # Drainage vulnerability (lower index = worse)
        drain_vuln = 1 - (self.drainage_index or 0.5)
        factors.append(drain_vuln * 0.20)

        # Population density vulnerability
        if self.population_density and self.population_density > 0:
            density_vuln = min(1, self.population_density / 35000)
            factors.append(density_vuln * 0.20)

        # Elderly vulnerability
        elder_vuln = min(1, (self.elderly_ratio or 0.1) / 0.25)
        factors.append(elder_vuln * 0.15)

        # Infrastructure vulnerability (less infra = more vulnerable)
        infra_vuln = 1 - min(1, (self.infrastructure_density or 0) / 10)
        factors.append(infra_vuln * 0.10)

        # Low-lying vulnerability
        factors.append((self.low_lying_index or 0.5) * 0.10)

        return min(1.0, sum(factors))

    def get_data_completeness(self) -> float:
        """Calculate data completeness score"""
        fields = [
            self.elevation_m, self.mean_slope, self.population,
            self.population_density, self.drainage_index,
            self.hospital_count, self.road_density_km,
            self.historical_flood_events, self.avg_annual_rainfall_mm,
        ]
        filled = sum(1 for f in fields if f is not None and f != 0)
        return filled / len(fields)


class WardRiskScore(Base):
    """
    Ward risk score with dual-layer risk assessment:
    Layer 1: Explainable composite
    Layer 2: ML calibration
    Final: Weighted fusion
    """
    __tablename__ = "ward_risk_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ward_id = Column(String(20), ForeignKey("wards.ward_id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Layer 1: Composite Risk (explainable formulas)
    flood_baseline_risk = Column(Float, default=0.0)
    flood_event_risk = Column(Float, default=0.0)
    flood_risk_delta = Column(Float, default=0.0)
    flood_risk_delta_pct = Column(Float, default=0.0)

    heat_baseline_risk = Column(Float, default=0.0)
    heat_event_risk = Column(Float, default=0.0)
    heat_risk_delta = Column(Float, default=0.0)
    heat_risk_delta_pct = Column(Float, default=0.0)

    # Layer 2: ML Calibrated Risk
    ml_flood_probability = Column(Float)  # XGBoost output
    ml_heat_probability = Column(Float)
    ml_confidence = Column(Float)  # model confidence

    # Final Fused Risk: 0.6*composite + 0.4*ML
    final_flood_risk = Column(Float, default=0.0)
    final_heat_risk = Column(Float, default=0.0)
    final_combined_risk = Column(Float, default=0.0)

    # Confidence and Uncertainty
    confidence_score = Column(Float, default=0.5)  # 0-1 based on data completeness + model confidence
    uncertainty_score = Column(Float, default=0.5)  # 0-1 based on missing data
    data_freshness_hours = Column(Float)  # hours since last weather data

    # Neighbor Spillover
    neighbor_spillover_applied = Column(Boolean, default=False)
    spillover_source_wards = Column(JSON)  # list of high-risk neighbor ward_ids

    # Weather Conditions (real data)
    current_rainfall_mm = Column(Float)
    rainfall_forecast_48h_mm = Column(Float)
    rainfall_forecast_7d_mm = Column(Float)
    current_temp_c = Column(Float)
    temp_anomaly_c = Column(Float)
    weather_condition = Column(String(50))
    wind_speed_kmh = Column(Float)
    humidity_pct = Column(Float)

    # Risk Factors & Explainability
    risk_factors = Column(JSON)  # detailed factor breakdown
    top_drivers = Column(JSON)  # top 5 contributing factors
    shap_values = Column(JSON)  # SHAP explainability values
    recommendations = Column(JSON)  # action recommendations

    # Alerts
    top_hazard = Column(String(20))
    top_risk_score = Column(Float, default=0.0)
    risk_category = Column(String(20))  # low, moderate, high, critical
    surge_alert = Column(Boolean, default=False)  # delta > 20%
    critical_alert = Column(Boolean, default=False)  # delta > 40%
    alert_message = Column(Text)

    # Relationships
    ward = relationship("Ward", back_populates="risk_scores")

    # Indexes
    __table_args__ = (
        Index("idx_risk_ward_time", "ward_id", "timestamp"),
        Index("idx_risk_category", "risk_category"),
        Index("idx_risk_alerts", "surge_alert", "critical_alert"),
    )

    def to_dict(self) -> dict:
        """Full API response format matching requirements"""
        return {
            "ward_id": self.ward_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            # Composite risk
            "baseline_risk": {
                "flood": round(self.flood_baseline_risk or 0, 2),
                "heat": round(self.heat_baseline_risk or 0, 2),
            },
            "event_risk": {
                "flood": round(self.flood_event_risk or 0, 2),
                "heat": round(self.heat_event_risk or 0, 2),
            },
            "delta": {
                "flood": round(self.flood_risk_delta or 0, 2),
                "flood_pct": round(self.flood_risk_delta_pct or 0, 2),
                "heat": round(self.heat_risk_delta or 0, 2),
                "heat_pct": round(self.heat_risk_delta_pct or 0, 2),
            },
            # ML risk
            "ml_risk": {
                "flood_probability": round(self.ml_flood_probability or 0, 4),
                "heat_probability": round(self.ml_heat_probability or 0, 4),
                "confidence": round(self.ml_confidence or 0, 4),
            },
            # Final fused risk
            "final_risk": {
                "flood": round(self.final_flood_risk or 0, 2),
                "heat": round(self.final_heat_risk or 0, 2),
                "combined": round(self.final_combined_risk or 0, 2),
            },
            "risk_category": self.risk_category,
            "confidence_score": round(self.confidence_score or 0, 4),
            "uncertainty_score": round(self.uncertainty_score or 0, 4),
            # Alerts
            "surge_alert": self.surge_alert,
            "critical_alert": self.critical_alert,
            "alert_message": self.alert_message,
            # Explainability
            "top_drivers": self.top_drivers or [],
            "shap_values": self.shap_values,
            "recommendations": self.recommendations or [],
            # Weather
            "weather": {
                "rainfall_mm": self.current_rainfall_mm,
                "rainfall_48h_mm": self.rainfall_forecast_48h_mm,
                "rainfall_7d_mm": self.rainfall_forecast_7d_mm,
                "temperature_c": self.current_temp_c,
                "temp_anomaly_c": self.temp_anomaly_c,
                "condition": self.weather_condition,
                "wind_speed_kmh": self.wind_speed_kmh,
                "humidity_pct": self.humidity_pct,
            },
            # Spillover
            "neighbor_spillover": {
                "applied": self.neighbor_spillover_applied,
                "source_wards": self.spillover_source_wards or [],
            },
            "top_hazard": self.top_hazard,
            "last_updated": self.timestamp.isoformat() if self.timestamp else None,
        }

    def get_risk_category(self, score: float = None) -> str:
        """Get risk category from score"""
        s = score or self.final_combined_risk or 0
        if s >= 80:
            return "critical"
        elif s >= 60:
            return "high"
        elif s >= 30:
            return "moderate"
        return "low"
