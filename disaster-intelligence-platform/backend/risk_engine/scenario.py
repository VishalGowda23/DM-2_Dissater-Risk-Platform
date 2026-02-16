"""
Scenario Simulation Engine
Allows dynamic modification of parameters to simulate "what-if" scenarios
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

from core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ScenarioParameters:
    """Parameters for scenario simulation"""
    name: str = "Default Scenario"
    
    # Weather modifiers
    rainfall_multiplier: float = 1.0  # 1.0 = no change, 1.2 = +20%
    temp_anomaly_addition: float = 0.0  # Additional temperature anomaly in Celsius
    
    # Infrastructure modifiers
    drainage_efficiency_multiplier: float = 1.0  # 1.0 = normal, 1.2 = improved
    
    # Demographic modifiers
    population_growth_pct: float = 0.0  # Percentage increase
    
    # Time modifiers
    forecast_hours: int = 48
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "rainfall_multiplier": self.rainfall_multiplier,
            "temp_anomaly_addition": self.temp_anomaly_addition,
            "drainage_efficiency_multiplier": self.drainage_efficiency_multiplier,
            "population_growth_pct": self.population_growth_pct,
            "forecast_hours": self.forecast_hours
        }


class ScenarioEngine:
    """
    Scenario Simulation Engine
    
    Allows users to modify parameters and see impact on risk scores
    and resource allocations.
    """
    
    # Predefined scenarios
    SCENARIOS = {
        "default": ScenarioParameters(name="Current Conditions"),
        "heavy_rain": ScenarioParameters(
            name="Heavy Rainfall (+50%)",
            rainfall_multiplier=1.5
        ),
        "extreme_rain": ScenarioParameters(
            name="Extreme Rainfall (+100%)",
            rainfall_multiplier=2.0
        ),
        "heatwave": ScenarioParameters(
            name="Heatwave (+4°C)",
            temp_anomaly_addition=4.0
        ),
        "extreme_heat": ScenarioParameters(
            name="Extreme Heat (+6°C)",
            temp_anomaly_addition=6.0
        ),
        "compound": ScenarioParameters(
            name="Compound Event (Rain + Heat)",
            rainfall_multiplier=1.3,
            temp_anomaly_addition=3.0
        ),
        "improved_drainage": ScenarioParameters(
            name="Improved Drainage (+20%)",
            drainage_efficiency_multiplier=1.2
        ),
        "population_growth": ScenarioParameters(
            name="Population Growth (+10%)",
            population_growth_pct=10.0
        ),
    }
    
    def __init__(self):
        self.current_scenario = self.SCENARIOS["default"]
    
    def get_available_scenarios(self) -> Dict[str, str]:
        """Get list of available predefined scenarios"""
        return {key: scenario.name for key, scenario in self.SCENARIOS.items()}
    
    def apply_scenario(
        self, 
        base_risk_data: Dict, 
        scenario: ScenarioParameters
    ) -> Dict:
        """
        Apply scenario parameters to base risk data
        
        Args:
            base_risk_data: Original risk data
            scenario: Scenario parameters to apply
            
        Returns:
            Modified risk data
        """
        modified = base_risk_data.copy()
        
        # Apply rainfall multiplier to flood risk
        if "flood_event_risk" in modified:
            original_flood = modified["flood_event_risk"]
            # Non-linear scaling: higher base risk = more sensitive to rainfall increase
            sensitivity = 0.5 + (original_flood / 200)  # 0.5 to 1.0
            flood_increase = (scenario.rainfall_multiplier - 1.0) * sensitivity * 100
            modified["flood_event_risk"] = min(100, original_flood + flood_increase)
            modified["flood_scenario_adjustment"] = round(flood_increase, 2)
        
        # Apply temperature anomaly to heat risk
        if "heat_event_risk" in modified:
            original_heat = modified["heat_event_risk"]
            # Each degree of additional anomaly adds to risk
            heat_increase = scenario.temp_anomaly_addition * 8  # ~8% per degree
            modified["heat_event_risk"] = min(100, original_heat + heat_increase)
            modified["heat_scenario_adjustment"] = round(heat_increase, 2)
        
        # Apply drainage efficiency improvement (reduces flood risk)
        if "flood_event_risk" in modified and scenario.drainage_efficiency_multiplier != 1.0:
            improvement = (scenario.drainage_efficiency_multiplier - 1.0) * 20
            modified["flood_event_risk"] = max(0, modified["flood_event_risk"] - improvement)
            modified["drainage_adjustment"] = round(-improvement, 2)
        
        # Apply population growth (increases vulnerability)
        if scenario.population_growth_pct > 0:
            if "population" in modified:
                growth_factor = 1 + (scenario.population_growth_pct / 100)
                modified["population"] = int(modified["population"] * growth_factor)
            
            # Slight increase in risk due to higher exposure
            exposure_increase = scenario.population_growth_pct * 0.3
            if "flood_event_risk" in modified:
                modified["flood_event_risk"] = min(100, modified["flood_event_risk"] + exposure_increase)
            if "heat_event_risk" in modified:
                modified["heat_event_risk"] = min(100, modified["heat_event_risk"] + exposure_increase)
        
        # Recalculate delta
        if "flood_baseline_risk" in modified and "flood_event_risk" in modified:
            modified["flood_risk_delta"] = (
                modified["flood_event_risk"] - modified["flood_baseline_risk"]
            )
        
        if "heat_baseline_risk" in modified and "heat_event_risk" in modified:
            modified["heat_risk_delta"] = (
                modified["heat_event_risk"] - modified["heat_baseline_risk"]
            )
        
        # Update top hazard
        flood_risk = modified.get("flood_event_risk", 0)
        heat_risk = modified.get("heat_event_risk", 0)
        
        if flood_risk > heat_risk and flood_risk > 30:
            modified["top_hazard"] = "flood"
            modified["top_risk_score"] = flood_risk
        elif heat_risk > flood_risk and heat_risk > 30:
            modified["top_hazard"] = "heat"
            modified["top_risk_score"] = heat_risk
        else:
            modified["top_hazard"] = "none"
            modified["top_risk_score"] = max(flood_risk, heat_risk)
        
        modified["scenario_applied"] = scenario.name
        modified["scenario_timestamp"] = datetime.now().isoformat()
        
        return modified
    
    def run_scenario_comparison(
        self,
        ward_data_list: List[Dict],
        scenario_key: str
    ) -> Dict:
        """
        Run scenario comparison for multiple wards
        
        Args:
            ward_data_list: List of ward risk data
            scenario_key: Key of scenario to apply
            
        Returns:
            Comparison results
        """
        if scenario_key not in self.SCENARIOS:
            return {"error": f"Unknown scenario: {scenario_key}"}
        
        scenario = self.SCENARIOS[scenario_key]
        
        baseline_results = []
        scenario_results = []
        
        for ward_data in ward_data_list:
            # Store baseline
            baseline_results.append(ward_data.copy())
            
            # Apply scenario
            modified = self.apply_scenario(ward_data, scenario)
            scenario_results.append(modified)
        
        # Calculate aggregate impact
        avg_flood_change = sum(
            s.get("flood_event_risk", 0) - b.get("flood_event_risk", 0)
            for s, b in zip(scenario_results, baseline_results)
        ) / len(ward_data_list) if ward_data_list else 0
        
        avg_heat_change = sum(
            s.get("heat_event_risk", 0) - b.get("heat_event_risk", 0)
            for s, b in zip(scenario_results, baseline_results)
        ) / len(ward_data_list) if ward_data_list else 0
        
        critical_increase = sum(
            1 for s, b in zip(scenario_results, baseline_results)
            if s.get("flood_event_risk", 0) > 80 and b.get("flood_event_risk", 0) <= 80
        )
        
        return {
            "scenario": scenario.to_dict(),
            "comparison": {
                "baseline": baseline_results,
                "scenario": scenario_results
            },
            "aggregate_impact": {
                "avg_flood_risk_change": round(avg_flood_change, 2),
                "avg_heat_risk_change": round(avg_heat_change, 2),
                "wards_newly_critical": critical_increase,
                "total_wards": len(ward_data_list)
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def create_custom_scenario(
        self,
        name: str,
        rainfall_multiplier: float = 1.0,
        temp_anomaly_addition: float = 0.0,
        drainage_efficiency_multiplier: float = 1.0,
        population_growth_pct: float = 0.0
    ) -> ScenarioParameters:
        """Create a custom scenario with specified parameters"""
        return ScenarioParameters(
            name=name,
            rainfall_multiplier=rainfall_multiplier,
            temp_anomaly_addition=temp_anomaly_addition,
            drainage_efficiency_multiplier=drainage_efficiency_multiplier,
            population_growth_pct=population_growth_pct
        )
    
    def get_scenario_impact_summary(
        self,
        baseline: Dict,
        scenario_result: Dict
    ) -> Dict:
        """Get a human-readable summary of scenario impact"""
        flood_change = scenario_result.get("flood_event_risk", 0) - baseline.get("flood_event_risk", 0)
        heat_change = scenario_result.get("heat_event_risk", 0) - baseline.get("heat_event_risk", 0)
        
        summary_parts = []
        
        if flood_change > 10:
            summary_parts.append(f"Flood risk increases significantly (+{flood_change:.0f}%)")
        elif flood_change > 0:
            summary_parts.append(f"Flood risk increases moderately (+{flood_change:.0f}%)")
        elif flood_change < -10:
            summary_parts.append(f"Flood risk decreases significantly ({flood_change:.0f}%)")
        
        if heat_change > 10:
            summary_parts.append(f"Heat risk increases significantly (+{heat_change:.0f}%)")
        elif heat_change > 0:
            summary_parts.append(f"Heat risk increases moderately (+{heat_change:.0f}%)")
        
        if not summary_parts:
            summary_parts.append("Minimal impact on risk levels")
        
        return {
            "summary": "; ".join(summary_parts),
            "flood_change": round(flood_change, 2),
            "heat_change": round(heat_change, 2),
            "recommendation": self._get_scenario_recommendation(flood_change, heat_change)
        }
    
    def _get_scenario_recommendation(
        self, 
        flood_change: float, 
        heat_change: float
    ) -> str:
        """Get recommendation based on scenario impact"""
        if flood_change > 20 or heat_change > 20:
            return "Urgent: Pre-position resources and alert response teams"
        elif flood_change > 10 or heat_change > 10:
            return "Advisory: Increase monitoring and prepare contingency plans"
        elif flood_change < -5 or heat_change < -5:
            return "Positive: Reduced risk allows resource reallocation"
        else:
            return "Maintain current preparedness levels"


# Singleton instance
scenario_engine = ScenarioEngine()
