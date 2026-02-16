"""
Historical disaster events model
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional

from core.database import Base


class HistoricalEvent(Base):
    """Historical disaster events for baseline risk calculation"""
    __tablename__ = "historical_events"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Event details
    event_type = Column(String(50), nullable=False, index=True)  # 'flood', 'heatwave', 'cyclone', 'landslide'
    event_date = Column(DateTime(timezone=True), nullable=False, index=True)
    event_year = Column(Integer, nullable=False, index=True)
    event_month = Column(Integer, nullable=True)
    
    # Location
    ward_id = Column(String(10), nullable=True, index=True)
    location_name = Column(String(200), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Impact data
    severity_score = Column(Float, nullable=True)  # 0-10 scale
    affected_people = Column(Integer, nullable=True)
    deaths = Column(Integer, nullable=True)
    injuries = Column(Integer, nullable=True)
    displaced = Column(Integer, nullable=True)
    
    # Infrastructure damage
    buildings_damaged = Column(Integer, nullable=True)
    roads_damaged_km = Column(Float, nullable=True)
    bridges_damaged = Column(Integer, nullable=True)
    
    # Economic impact
    economic_loss_inr = Column(Float, nullable=True)
    
    # Environmental data at time of event
    rainfall_mm = Column(Float, nullable=True)
    max_temperature_c = Column(Float, nullable=True)
    river_level_m = Column(Float, nullable=True)
    
    # Source and verification
    source = Column(String(200), nullable=True)  # News, government report, etc.
    source_url = Column(Text, nullable=True)
    verified = Column(String(20), default="unverified")  # verified, unverified, disputed
    
    # Description
    description = Column(Text, nullable=True)
    response_actions = Column(Text, nullable=True)
    
    # Metadata
    data_quality_score = Column(Float, nullable=True)  # 0-1
    additional_data = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self) -> dict:
        """Convert event to dictionary"""
        return {
            "id": self.id,
            "event_type": self.event_type,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "event_year": self.event_year,
            "ward_id": self.ward_id,
            "location_name": self.location_name,
            "severity_score": self.severity_score,
            "affected_people": self.affected_people,
            "deaths": self.deaths,
            "injuries": self.injuries,
            "rainfall_mm": self.rainfall_mm,
            "max_temperature_c": self.max_temperature_c,
            "source": self.source,
            "verified": self.verified,
            "description": self.description,
        }


class SeasonalBaseline(Base):
    """Seasonal baseline data for risk comparison"""
    __tablename__ = "seasonal_baselines"
    
    id = Column(Integer, primary_key=True, index=True)
    ward_id = Column(String(10), nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)  # 1-12
    
    # Historical averages
    avg_rainfall_mm = Column(Float, nullable=True)
    max_rainfall_mm = Column(Float, nullable=True)
    avg_temperature_c = Column(Float, nullable=True)
    max_temperature_c = Column(Float, nullable=True)
    min_temperature_c = Column(Float, nullable=True)
    
    # Historical event frequency
    avg_flood_events = Column(Float, nullable=True)  # per month average
    avg_heatwave_days = Column(Float, nullable=True)  # per month average
    
    # Computed from 10-year data
    flood_frequency_index = Column(Float, nullable=True)  # 0-1
    heat_frequency_index = Column(Float, nullable=True)  # 0-1
    
    # Data period
    data_start_year = Column(Integer, nullable=True)
    data_end_year = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self) -> dict:
        """Convert baseline to dictionary"""
        return {
            "ward_id": self.ward_id,
            "month": self.month,
            "avg_rainfall_mm": self.avg_rainfall_mm,
            "avg_temperature_c": self.avg_temperature_c,
            "flood_frequency_index": self.flood_frequency_index,
            "heat_frequency_index": self.heat_frequency_index,
        }
