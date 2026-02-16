"""
Baseline risk calculation module
Computes seasonal baseline risk using historical data and physical characteristics
"""
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime
import logging

from models.ward import Ward
from core.config import settings

logger = logging.getLogger(__name__)


class BaselineRiskCalculator:
    """Calculate baseline risk scores for wards"""
    
    def __init__(self):
        self.flood_weights = settings.FLOOD_BASELINE_WEIGHTS
        self.heat_weights = {
            "historical_heatwave_days": 0.50,
            "elderly_ratio": 0.30,
            "population_density": 0.20
        }
    
    def normalize(self, value: float, min_val: float, max_val: float) -> float:
        """Normalize value to 0-1 range using min-max scaling"""
        if max_val == min_val:
            return 0.5
        normalized = (value - min_val) / (max_val - min_val)
        return max(0.0, min(1.0, normalized))
    
    def calculate_historical_frequency_score(self, ward: Ward, all_wards: List[Ward]) -> float:
        """Calculate normalized historical flood frequency score"""
        if not all_wards:
            return 0.5
        
        frequencies = [w.historical_flood_count_10y or 0 for w in all_wards]
        min_freq = min(frequencies)
        max_freq = max(frequencies)
        
        ward_freq = ward.historical_flood_count_10y or 0
        return self.normalize(ward_freq, min_freq, max_freq)
    
    def calculate_elevation_vulnerability(self, ward: Ward, all_wards: List[Ward]) -> float:
        """Calculate elevation vulnerability (lower elevation = higher vulnerability)"""
        if ward.mean_elevation_m is None:
            return 0.5
        
        # Get elevation range from all wards
        elevations = [w.mean_elevation_m for w in all_wards if w.mean_elevation_m is not None]
        if not elevations:
            return 0.5
        
        min_elev = min(elevations)
        max_elev = max(elevations)
        
        # Lower elevation = higher vulnerability (invert)
        if max_elev == min_elev:
            return 0.5
        
        normalized = (ward.mean_elevation_m - min_elev) / (max_elev - min_elev)
        return 1.0 - normalized  # Invert: lower elevation = higher vulnerability
    
    def calculate_drainage_weakness(self, ward: Ward) -> float:
        """Calculate drainage weakness score"""
        if ward.drainage_index is None:
            # Use impervious surface as proxy
            if ward.impervious_surface_pct is not None:
                return ward.impervious_surface_pct / 100.0
            return 0.5
        
        # Drainage index: higher = better drainage, so invert for weakness
        return 1.0 - ward.drainage_index
    
    def calculate_flood_baseline(self, ward: Ward, all_wards: List[Ward]) -> float:
        """
        Calculate baseline flood risk for a ward
        Formula: 0.50*Historical_Frequency + 0.30*Elevation_Vulnerability + 0.20*Drainage_Weakness
        Returns: 0-100 risk score
        """
        try:
            # Historical frequency (0-1)
            hist_freq = self.calculate_historical_frequency_score(ward, all_wards)
            
            # Elevation vulnerability (0-1)
            elev_vuln = self.calculate_elevation_vulnerability(ward, all_wards)
            
            # Drainage weakness (0-1)
            drainage_weak = self.calculate_drainage_weakness(ward)
            
            # Weighted sum
            risk = (
                self.flood_weights["historical_frequency"] * hist_freq +
                self.flood_weights["elevation_vulnerability"] * elev_vuln +
                self.flood_weights["drainage_weakness"] * drainage_weak
            )
            
            # Scale to 0-100
            return round(risk * 100, 2)
            
        except Exception as e:
            logger.error(f"Error calculating flood baseline for ward {ward.ward_id}: {e}")
            return 50.0  # Default moderate risk
    
    def calculate_heatwave_baseline(self, ward: Ward, all_wards: List[Ward]) -> float:
        """
        Calculate baseline heatwave risk for a ward
        Formula: 0.50*Historical_Heatwave_Days + 0.30*Elderly_Ratio + 0.20*Density
        Returns: 0-100 risk score
        """
        try:
            # Historical heatwave days
            heat_days_list = [w.historical_heatwave_days_10y or 0 for w in all_wards]
            min_days = min(heat_days_list) if heat_days_list else 0
            max_days = max(heat_days_list) if heat_days_list else 1
            ward_days = ward.historical_heatwave_days_10y or 0
            hist_heat = self.normalize(ward_days, min_days, max_days)
            
            # Elderly ratio
            elderly_list = [w.elderly_ratio or 0 for w in all_wards]
            min_elderly = min(elderly_list) if elderly_list else 0
            max_elderly = max(elderly_list) if elderly_list else 0.2
            ward_elderly = ward.elderly_ratio or 0
            elderly_score = self.normalize(ward_elderly, min_elderly, max_elderly)
            
            # Population density
            density_list = [w.population_density or 0 for w in all_wards]
            min_density = min(density_list) if density_list else 0
            max_density = max(density_list) if density_list else 20000
            ward_density = ward.population_density or 0
            density_score = self.normalize(ward_density, min_density, max_density)
            
            # Weighted sum
            risk = (
                self.heat_weights["historical_heatwave_days"] * hist_heat +
                self.heat_weights["elderly_ratio"] * elderly_score +
                self.heat_weights["population_density"] * density_score
            )
            
            return round(risk * 100, 2)
            
        except Exception as e:
            logger.error(f"Error calculating heat baseline for ward {ward.ward_id}: {e}")
            return 50.0
    
    def calculate_all_baselines(self, wards: List[Ward]) -> Dict[str, Dict[str, float]]:
        """Calculate baseline risks for all wards"""
        results = {}
        
        for ward in wards:
            results[ward.ward_id] = {
                "flood_baseline": self.calculate_flood_baseline(ward, wards),
                "heat_baseline": self.calculate_heatwave_baseline(ward, wards),
            }
        
        return results
    
    def get_risk_category(self, risk_score: float) -> str:
        """Get risk category from score"""
        if risk_score <= settings.RISK_LOW_THRESHOLD:
            return "low"
        elif risk_score <= settings.RISK_MODERATE_THRESHOLD:
            return "moderate"
        elif risk_score <= settings.RISK_HIGH_THRESHOLD:
            return "high"
        else:
            return "critical"
