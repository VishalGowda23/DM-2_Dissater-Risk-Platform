"""
Risk Explainability Module
Provides detailed explanations for risk scores and top contributing factors
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

from core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class RiskFactor:
    """Individual risk factor contribution"""
    name: str
    value: float
    normalized_value: float
    weight: float
    contribution: float  # To final score (0-100)
    description: str


class RiskExplainer:
    """Generate explanations for risk scores"""
    
    def __init__(self):
        self.flood_factor_names = {
            "rainfall_intensity": "Forecast Rainfall Intensity",
            "cumulative_rain": "48-Hour Cumulative Rainfall",
            "baseline_vulnerability": "Baseline Vulnerability",
            "historical_frequency": "Historical Flood Frequency",
            "elevation_vulnerability": "Elevation Vulnerability",
            "drainage_weakness": "Drainage Weakness"
        }
        
        self.heat_factor_names = {
            "temperature_anomaly": "Temperature Anomaly",
            "baseline_vulnerability": "Baseline Vulnerability",
            "historical_heatwave_days": "Historical Heatwave Frequency",
            "elderly_ratio": "Elderly Population Ratio",
            "population_density": "Population Density"
        }
    
    def explain_flood_risk(
        self,
        baseline_risk: float,
        event_risk: float,
        baseline_factors: Dict,
        event_factors: Dict,
        ward_data: Dict
    ) -> Dict:
        """
        Generate explanation for flood risk
        
        Returns:
            Detailed explanation with top factors
        """
        delta = event_risk - baseline_risk
        delta_pct = (delta / baseline_risk * 100) if baseline_risk > 0 else 0
        
        # Determine surge level
        surge_level = "normal"
        surge_description = "Risk levels within normal range"
        
        if delta > settings.DELTA_CRITICAL_THRESHOLD:
            surge_level = "critical"
            surge_description = "CRITICAL SURGE: Immediate action required"
        elif delta > settings.DELTA_ESCALATION_THRESHOLD:
            surge_level = "escalation"
            surge_description = "ESCALATION ALERT: Risk significantly above baseline"
        
        # Extract top contributing factors from event risk
        event_factor_list = []
        for key, data in event_factors.items():
            if isinstance(data, dict) and "contribution" in data:
                event_factor_list.append({
                    "factor": self.flood_factor_names.get(key, key),
                    "contribution": data["contribution"],
                    "value": data.get("value", 0),
                    "weight": data.get("weight", 0)
                })
        
        # Sort by contribution
        event_factor_list.sort(key=lambda x: x["contribution"], reverse=True)
        top_event_factors = event_factor_list[:3]
        
        # Extract baseline factors
        baseline_factor_list = []
        for key, data in baseline_factors.items():
            if isinstance(data, dict) and "contribution" in data:
                baseline_factor_list.append({
                    "factor": self.flood_factor_names.get(key, key),
                    "contribution": data["contribution"],
                    "value": data.get("value", 0),
                    "weight": data.get("weight", 0)
                })
        
        baseline_factor_list.sort(key=lambda x: x["contribution"], reverse=True)
        top_baseline_factors = baseline_factor_list[:3]
        
        # Generate narrative
        narrative = self._generate_flood_narrative(
            ward_data, baseline_risk, event_risk, delta, top_event_factors
        )
        
        return {
            "ward_id": ward_data.get("ward_id"),
            "ward_name": ward_data.get("ward_name"),
            "hazard": "flood",
            "baseline_risk": round(baseline_risk, 1),
            "event_risk": round(event_risk, 1),
            "delta": round(delta, 1),
            "delta_pct": round(delta_pct, 1),
            "surge_level": surge_level,
            "surge_description": surge_description,
            "top_drivers_event": top_event_factors,
            "top_drivers_baseline": top_baseline_factors,
            "narrative": narrative,
            "recommendations": self._generate_flood_recommendations(event_risk, surge_level, ward_data)
        }
    
    def explain_heat_risk(
        self,
        baseline_risk: float,
        event_risk: float,
        baseline_factors: Dict,
        event_factors: Dict,
        ward_data: Dict
    ) -> Dict:
        """Generate explanation for heatwave risk"""
        delta = event_risk - baseline_risk
        delta_pct = (delta / baseline_risk * 100) if baseline_risk > 0 else 0
        
        surge_level = "normal"
        surge_description = "Risk levels within normal range"
        
        if delta > settings.DELTA_CRITICAL_THRESHOLD:
            surge_level = "critical"
            surge_description = "CRITICAL HEAT SURGE: Immediate cooling measures required"
        elif delta > settings.DELTA_ESCALATION_THRESHOLD:
            surge_level = "escalation"
            surge_description = "HEAT ESCALATION: Enhanced monitoring required"
        
        # Extract top factors
        event_factor_list = []
        for key, data in event_factors.items():
            if isinstance(data, dict) and "contribution" in data:
                event_factor_list.append({
                    "factor": self.heat_factor_names.get(key, key),
                    "contribution": data["contribution"],
                    "value": data.get("value", 0),
                    "weight": data.get("weight", 0)
                })
        
        event_factor_list.sort(key=lambda x: x["contribution"], reverse=True)
        top_event_factors = event_factor_list[:3]
        
        narrative = self._generate_heat_narrative(
            ward_data, baseline_risk, event_risk, delta, top_event_factors
        )
        
        return {
            "ward_id": ward_data.get("ward_id"),
            "ward_name": ward_data.get("ward_name"),
            "hazard": "heat",
            "baseline_risk": round(baseline_risk, 1),
            "event_risk": round(event_risk, 1),
            "delta": round(delta, 1),
            "delta_pct": round(delta_pct, 1),
            "surge_level": surge_level,
            "surge_description": surge_description,
            "top_drivers_event": top_event_factors,
            "top_drivers_baseline": [],
            "narrative": narrative,
            "recommendations": self._generate_heat_recommendations(event_risk, surge_level, ward_data)
        }
    
    def _generate_flood_narrative(
        self, 
        ward_data: Dict, 
        baseline: float, 
        event: float, 
        delta: float,
        top_factors: List[Dict]
    ) -> str:
        """Generate human-readable narrative for flood risk"""
        ward_name = ward_data.get("ward_name", ward_data.get("ward_id", "This ward"))
        
        if delta > settings.DELTA_CRITICAL_THRESHOLD:
            return (
                f"{ward_name} is experiencing a CRITICAL flood risk surge. "
                f"Current risk ({event:.0f}%) is {delta:.0f} percentage points above baseline ({baseline:.0f}%). "
                f"Primary driver: {top_factors[0]['factor'] if top_factors else 'heavy rainfall'}. "
                f"Immediate evacuation and resource deployment recommended."
            )
        elif delta > settings.DELTA_ESCALATION_THRESHOLD:
            return (
                f"{ward_name} shows elevated flood risk. "
                f"Current risk ({event:.0f}%) exceeds baseline ({baseline:.0f}%) by {delta:.0f} points. "
                f"Key factor: {top_factors[0]['factor'] if top_factors else 'increased rainfall'}. "
                f"Pre-position resources and alert response teams."
            )
        else:
            return (
                f"{ward_name} flood risk is near baseline levels. "
                f"Current risk: {event:.0f}%, Baseline: {baseline:.0f}%. "
                f"Maintain normal monitoring procedures."
            )
    
    def _generate_heat_narrative(
        self, 
        ward_data: Dict, 
        baseline: float, 
        event: float, 
        delta: float,
        top_factors: List[Dict]
    ) -> str:
        """Generate human-readable narrative for heat risk"""
        ward_name = ward_data.get("ward_name", ward_data.get("ward_id", "This ward"))
        
        if delta > settings.DELTA_CRITICAL_THRESHOLD:
            return (
                f"{ward_name} is under CRITICAL heat stress. "
                f"Risk level ({event:.0f}%) is {delta:.0f} points above baseline ({baseline:.0f}%). "
                f"Activate cooling centers and issue heat alerts immediately."
            )
        elif delta > settings.DELTA_ESCALATION_THRESHOLD:
            return (
                f"{ward_name} experiencing elevated heat risk. "
                f"Current risk ({event:.0f}%) exceeds baseline by {delta:.0f} points. "
                f"Prepare cooling infrastructure and vulnerable population outreach."
            )
        else:
            return (
                f"{ward_name} heat risk at normal levels. "
                f"Current: {event:.0f}%, Baseline: {baseline:.0f}%."
            )
    
    def _generate_flood_recommendations(
        self, 
        risk: float, 
        surge_level: str, 
        ward_data: Dict
    ) -> List[str]:
        """Generate flood-specific recommendations"""
        recommendations = []
        
        if risk > 80:
            recommendations.extend([
                "Immediate evacuation of low-lying areas",
                "Deploy all available pumps to critical locations",
                "Open relief camps and mobilize buses",
                "Alert medical teams for emergency response"
            ])
        elif risk > 60:
            recommendations.extend([
                "Pre-position pumps and sandbags",
                "Alert relief camp managers",
                "Monitor water levels hourly",
                "Prepare vulnerable population for possible evacuation"
            ])
        elif risk > 30:
            recommendations.extend([
                "Increase monitoring frequency",
                "Verify drainage clearance",
                "Brief response teams"
            ])
        else:
            recommendations.append("Maintain normal monitoring")
        
        return recommendations
    
    def _generate_heat_recommendations(
        self, 
        risk: float, 
        surge_level: str, 
        ward_data: Dict
    ) -> List[str]:
        """Generate heat-specific recommendations"""
        recommendations = []
        
        elderly_ratio = ward_data.get("elderly_ratio", 0)
        
        if risk > 80:
            recommendations.extend([
                "Activate all cooling centers immediately",
                "Issue public heat alert",
                "Deploy mobile medical units",
                "Conduct vulnerable population check-ins"
            ])
        elif risk > 60:
            recommendations.extend([
                "Open designated cooling centers",
                "Distribute water at public locations",
                "Alert healthcare facilities"
            ])
        
        if elderly_ratio > 0.1:
            recommendations.append("Priority outreach to elderly population")
        
        return recommendations
    
    def compare_scenarios(
        self,
        ward_id: str,
        baseline_scenario: Dict,
        modified_scenario: Dict,
        modifications: Dict
    ) -> Dict:
        """Compare risk between two scenarios"""
        return {
            "ward_id": ward_id,
            "modifications": modifications,
            "baseline": baseline_scenario,
            "modified": modified_scenario,
            "impact": {
                "flood_risk_change": modified_scenario.get("flood_risk", 0) - baseline_scenario.get("flood_risk", 0),
                "heat_risk_change": modified_scenario.get("heat_risk", 0) - baseline_scenario.get("heat_risk", 0),
                "resource_need_change": "increased" if modified_scenario.get("flood_risk", 0) > baseline_scenario.get("flood_risk", 0) else "stable"
            }
        }


# Singleton instance
explainer = RiskExplainer()
