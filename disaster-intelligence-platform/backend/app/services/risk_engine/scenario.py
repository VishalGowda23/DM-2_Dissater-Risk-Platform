"""
Scenario Engine for what-if simulations
Modify feature vectors dynamically and recompute risk without retraining
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
import logging

from app.db.config import settings
from app.services.risk_engine.composite import CompositeRiskCalculator

logger = logging.getLogger(__name__)


@dataclass
class ScenarioParameters:
    """Adjustable scenario parameters"""
    rain_multiplier: float = 1.0
    temperature_increase: float = 0.0
    drainage_improvement: float = 0.0        # fraction improvement (0-1)
    infrastructure_failure_factor: float = 0.0  # fraction of infra failing (0-1)
    population_growth_pct: float = 0.0
    custom_label: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# 8 predefined scenarios
AVAILABLE_SCENARIOS = {
    "heavy_rain": ScenarioParameters(rain_multiplier=2.0, custom_label="Heavy Rainfall (2x)"),
    "extreme_rain": ScenarioParameters(rain_multiplier=3.5, custom_label="Extreme Rainfall (3.5x)"),
    "cloudburst": ScenarioParameters(rain_multiplier=5.0, custom_label="Cloudburst (5x+)"),
    "moderate_heatwave": ScenarioParameters(temperature_increase=3.0, custom_label="Moderate Heatwave (+3°C)"),
    "severe_heatwave": ScenarioParameters(temperature_increase=6.0, custom_label="Severe Heatwave (+6°C)"),
    "compound_disaster": ScenarioParameters(
        rain_multiplier=2.5, temperature_increase=2.0,
        custom_label="Compound: Rain + Heat"
    ),
    "improved_drainage": ScenarioParameters(drainage_improvement=0.3, custom_label="Drainage Improvement (+30%)"),
    "infrastructure_failure": ScenarioParameters(
        infrastructure_failure_factor=0.5,
        custom_label="50% Infrastructure Failure"
    ),
}


class ScenarioEngine:
    """
    Scenario simulation engine
    Modifies feature vectors and recomputes risk without retraining ML model
    """

    def __init__(self):
        self.composite = CompositeRiskCalculator()

    def get_available_scenarios(self) -> Dict[str, Dict]:
        """Return all available scenario presets"""
        return {k: v.to_dict() for k, v in AVAILABLE_SCENARIOS.items()}

    def apply_scenario(self, ward, params: ScenarioParameters,
                        weather_data: Optional[Dict] = None,
                        baseline_flood: float = 50.0,
                        baseline_heat: float = 50.0) -> Dict:
        """
        Apply scenario parameters and recompute risk
        Modifies weather/ward features in-place (copies), does NOT retrain
        """
        # Deep copy weather data
        modified_weather = self._modify_weather(weather_data, params)

        # Modify ward features (create a proxy)
        modified_ward = self._modify_ward(ward, params)

        # Recalculate flood event risk
        flood_result = self.composite.calculate_flood_event_risk(
            modified_ward, modified_weather,
            baseline_vulnerability=baseline_flood / 100
        )

        # Recalculate heat event risk
        heat_result = self.composite.calculate_heat_event_risk(
            modified_ward, modified_weather,
            baseline_vulnerability=baseline_heat / 100
        )

        scenario_flood = flood_result["event_risk"]
        scenario_heat = heat_result["event_risk"]

        # Apply non-linear rainfall sensitivity
        if params.rain_multiplier > 1:
            sensitivity = 1.0 + 0.3 * (params.rain_multiplier - 1) ** 1.2
            scenario_flood = min(100, scenario_flood * sensitivity / params.rain_multiplier)

        # Infrastructure failure increases both risks
        if params.infrastructure_failure_factor > 0:
            failure_boost = 1 + params.infrastructure_failure_factor * 0.4
            scenario_flood = min(100, scenario_flood * failure_boost)
            scenario_heat = min(100, scenario_heat * failure_boost)

        # Drainage improvement reduces flood risk
        if params.drainage_improvement > 0:
            reduction = 1 - params.drainage_improvement * 0.5
            scenario_flood = max(0, scenario_flood * reduction)

        # Cap results
        scenario_flood = round(min(100, max(0, scenario_flood)), 2)
        scenario_heat = round(min(100, max(0, scenario_heat)), 2)

        return {
            "ward_id": ward.ward_id,
            "ward_name": ward.name,
            "scenario_params": params.to_dict(),
            "baseline": {
                "flood": baseline_flood,
                "heat": baseline_heat,
            },
            "scenario_risk": {
                "flood": scenario_flood,
                "heat": scenario_heat,
                "combined": max(scenario_flood, scenario_heat),
            },
            "delta": {
                "flood": round(scenario_flood - baseline_flood, 2),
                "heat": round(scenario_heat - baseline_heat, 2),
            },
            "risk_category": self.composite.get_risk_category(max(scenario_flood, scenario_heat)),
        }

    def run_scenario_comparison(self, wards, scenario_key: str = None,
                                  custom_params: ScenarioParameters = None,
                                  weather_data: Dict[str, Dict] = None) -> Dict:
        """
        Run scenario across all wards and return comparison
        weather_data: dict mapping ward_id -> weather_data
        """
        if scenario_key:
            if scenario_key not in AVAILABLE_SCENARIOS:
                raise ValueError(f"Unknown scenario: {scenario_key}. Available: {list(AVAILABLE_SCENARIOS.keys())}")
            params = AVAILABLE_SCENARIOS[scenario_key]
        elif custom_params:
            params = custom_params
        else:
            params = ScenarioParameters()

        all_wards_list = list(wards)
        results = []
        total_flood_delta = 0
        total_heat_delta = 0
        critical_count = 0

        for ward in all_wards_list:
            # Get current baselines
            baseline_flood = self.composite.calculate_flood_baseline(ward, all_wards_list)
            baseline_heat = self.composite.calculate_heatwave_baseline(ward, all_wards_list)

            ward_weather = weather_data.get(ward.ward_id) if weather_data else None

            ward_result = self.apply_scenario(
                ward, params, ward_weather,
                baseline_flood, baseline_heat
            )
            results.append(ward_result)

            total_flood_delta += ward_result["delta"]["flood"]
            total_heat_delta += ward_result["delta"]["heat"]

            if ward_result["risk_category"] in ["high", "critical"]:
                critical_count += 1

        n = len(results)
        avg_flood_delta = round(total_flood_delta / n, 2) if n > 0 else 0
        avg_heat_delta = round(total_heat_delta / n, 2) if n > 0 else 0

        return {
            "scenario": params.to_dict(),
            "scenario_key": scenario_key,
            "ward_results": results,
            "summary": {
                "wards_analyzed": n,
                "avg_flood_risk_change": avg_flood_delta,
                "avg_heat_risk_change": avg_heat_delta,
                "critical_wards": critical_count,
                "impact_level": self._impact_level(avg_flood_delta, avg_heat_delta),
            },
            "recommendations": self._scenario_recommendations(params, avg_flood_delta, avg_heat_delta),
        }

    def _modify_weather(self, weather_data: Optional[Dict], params: ScenarioParameters) -> Optional[Dict]:
        """Create modified weather data for scenario"""
        if weather_data is None:
            # Create synthetic weather for scenario analysis
            return {
                "current": {
                    "rainfall_mm": 10 * params.rain_multiplier,
                    "temperature_c": 28 + params.temperature_increase,
                    "humidity_pct": 70,
                    "wind_speed_kmh": 15,
                    "condition": "scenario_simulation",
                },
                "forecast": {
                    "rainfall_48h_mm": 30 * params.rain_multiplier,
                    "rainfall_7d_mm": 60 * params.rain_multiplier,
                    "max_rainfall_intensity_mm_h": 20 * params.rain_multiplier,
                    "avg_temp_forecast_c": 28 + params.temperature_increase,
                },
            }

        # Deep copy and modify
        modified = {
            "current": dict(weather_data.get("current", {})),
            "forecast": dict(weather_data.get("forecast", {})),
        }

        # Apply rain multiplier
        if params.rain_multiplier != 1.0:
            c = modified["current"]
            f = modified["forecast"]
            c["rainfall_mm"] = (c.get("rainfall_mm", 0) or 0) * params.rain_multiplier
            f["rainfall_48h_mm"] = (f.get("rainfall_48h_mm", 0) or 0) * params.rain_multiplier
            f["rainfall_7d_mm"] = (f.get("rainfall_7d_mm", 0) or 0) * params.rain_multiplier
            f["max_rainfall_intensity_mm_h"] = (f.get("max_rainfall_intensity_mm_h", 0) or 0) * params.rain_multiplier

        # Apply temperature increase
        if params.temperature_increase != 0:
            c = modified["current"]
            f = modified["forecast"]
            if c.get("temperature_c"):
                c["temperature_c"] += params.temperature_increase
            if f.get("avg_temp_forecast_c"):
                f["avg_temp_forecast_c"] += params.temperature_increase

        return modified

    def _modify_ward(self, ward, params: ScenarioParameters):
        """Create a proxy ward with modified attributes"""
        class WardProxy:
            pass

        proxy = WardProxy()
        # Copy all attributes
        for attr in dir(ward):
            if not attr.startswith("_"):
                try:
                    setattr(proxy, attr, getattr(ward, attr))
                except Exception:
                    pass

        # Apply modifications
        if params.drainage_improvement > 0:
            current = getattr(proxy, "drainage_index", 0.5) or 0.5
            proxy.drainage_index = min(1.0, current + params.drainage_improvement)

        if params.population_growth_pct > 0:
            pop = getattr(proxy, "population", 100000) or 100000
            proxy.population = int(pop * (1 + params.population_growth_pct / 100))
            area = getattr(proxy, "area_sq_km", 10) or 10
            proxy.population_density = proxy.population / area

        if params.infrastructure_failure_factor > 0:
            infra = getattr(proxy, "infrastructure_density", 5) or 5
            proxy.infrastructure_density = infra * (1 - params.infrastructure_failure_factor)

        return proxy

    @staticmethod
    def _impact_level(flood_delta: float, heat_delta: float) -> str:
        max_delta = max(abs(flood_delta), abs(heat_delta))
        if max_delta > 30:
            return "severe"
        elif max_delta > 15:
            return "significant"
        elif max_delta > 5:
            return "moderate"
        return "minimal"

    @staticmethod
    def _scenario_recommendations(params: ScenarioParameters,
                                   flood_delta: float, heat_delta: float) -> List[str]:
        recs = []
        if flood_delta > 20:
            recs.append("Deploy additional flood response resources preemptively")
            recs.append("Activate early warning systems across all critical wards")
        if heat_delta > 15:
            recs.append("Open additional cooling centers in high-impact wards")
            recs.append("Issue heat advisory for vulnerable populations")
        if params.infrastructure_failure_factor > 0.3:
            recs.append("Implement infrastructure redundancy plans")
        if params.drainage_improvement > 0:
            recs.append(f"Targeted drainage improvement reduces flood risk by ~{round(flood_delta, 1)} points on average")
        if not recs:
            recs.append("Scenario impact is within manageable range")
        return recs


# Global instance
scenario_engine = ScenarioEngine()
