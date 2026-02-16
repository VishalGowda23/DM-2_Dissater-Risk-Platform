"""
Resource allocation models
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text, Boolean
from sqlalchemy.sql import func
from datetime import datetime

from core.database import Base


class ResourceType(Base):
    """Types of disaster response resources"""
    __tablename__ = "resource_types"
    
    id = Column(Integer, primary_key=True, index=True)
    resource_code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Resource category
    category = Column(String(50), nullable=False)  # 'flood', 'heat', 'medical', 'transport', 'shelter'
    
    # Effectiveness metrics
    effectiveness_flood = Column(Float, default=0.0)  # 0-1
    effectiveness_heat = Column(Float, default=0.0)  # 0-1
    people_served_per_unit = Column(Integer, nullable=True)  # How many people can one unit serve
    
    # Cost and logistics
    cost_per_unit_inr = Column(Float, nullable=True)
    deployment_time_hours = Column(Float, nullable=True)
    requires_training = Column(Boolean, default=False)
    
    # Metadata
    icon_url = Column(String(200), nullable=True)
    additional_data = Column(JSON, default=dict)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "resource_code": self.resource_code,
            "name": self.name,
            "category": self.category,
            "effectiveness_flood": self.effectiveness_flood,
            "effectiveness_heat": self.effectiveness_heat,
            "people_served_per_unit": self.people_served_per_unit,
        }


class ResourceAllocation(Base):
    """Resource allocation recommendations"""
    __tablename__ = "resource_allocations"
    
    id = Column(Integer, primary_key=True, index=True)
    allocation_id = Column(String(50), unique=True, nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Scenario parameters
    scenario_name = Column(String(100), nullable=True)
    rainfall_multiplier = Column(Float, default=1.0)
    temp_anomaly_addition = Column(Float, default=0.0)
    
    # Ward allocation
    ward_id = Column(String(10), nullable=False, index=True)
    ward_name = Column(String(100), nullable=True)
    
    # Risk context
    flood_risk = Column(Float, nullable=True)
    heat_risk = Column(Float, nullable=True)
    population = Column(Integer, nullable=True)
    need_score = Column(Float, nullable=True)
    
    # Allocated resources
    pumps_allocated = Column(Integer, default=0)
    buses_allocated = Column(Integer, default=0)
    relief_camps_allocated = Column(Integer, default=0)
    cooling_centers_allocated = Column(Integer, default=0)
    medical_units_allocated = Column(Integer, default=0)
    
    # Explanation
    allocation_reason = Column(Text, nullable=True)
    expected_impact = Column(Text, nullable=True)
    
    # Metadata
    additional_data = Column(JSON, default=dict)
    
    def to_dict(self) -> dict:
        return {
            "allocation_id": self.allocation_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "scenario": self.scenario_name,
            "ward_id": self.ward_id,
            "ward_name": self.ward_name,
            "risk_context": {
                "flood_risk": self.flood_risk,
                "heat_risk": self.heat_risk,
                "population": self.population,
                "need_score": self.need_score,
            },
            "allocations": {
                "pumps": self.pumps_allocated,
                "buses": self.buses_allocated,
                "relief_camps": self.relief_camps_allocated,
                "cooling_centers": self.cooling_centers_allocated,
                "medical_units": self.medical_units_allocated,
            },
            "explanation": self.allocation_reason,
            "expected_impact": self.expected_impact,
        }


class ResourceInventory(Base):
    """Current resource inventory available for allocation"""
    __tablename__ = "resource_inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    
    # Available quantities
    total_available = Column(Integer, default=0)
    currently_deployed = Column(Integer, default=0)
    in_maintenance = Column(Integer, default=0)
    
    # Location
    storage_location = Column(String(200), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Contact
    contact_person = Column(String(100), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    
    # Last updated
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    
    def get_available_for_deployment(self) -> int:
        """Get number of units available for deployment"""
        return self.total_available - self.currently_deployed - self.in_maintenance
    
    def to_dict(self) -> dict:
        return {
            "resource_type": self.resource_type,
            "total_available": self.total_available,
            "currently_deployed": self.currently_deployed,
            "in_maintenance": self.in_maintenance,
            "available_for_deployment": self.get_available_for_deployment(),
            "storage_location": self.storage_location,
            "contact": {
                "person": self.contact_person,
                "phone": self.contact_phone,
            },
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }
