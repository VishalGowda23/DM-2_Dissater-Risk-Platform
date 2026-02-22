"""
Layer 1: Explainable Composite Risk Calculator
Implements the required formulas for flood and heat risk
"""
from typing import Dict, List, Optional
import logging

from app.db.config import settings

logger = logging.getLogger(__name__)


class CompositeRiskCalculator:
    """
    Explainable composite risk using weighted formulas:
    
    Flood Baseline = 0.50*Historical + 0.30*Elevation + 0.20*(1-Drainage)
    Flood Event    = 0.60*Forecast + 0.20*Cumulative48h + 0.20*Baseline
    Heat Event     = 0.70*TempAnomaly + 0.30*BaselineVulnerability
    Risk Delta     = Event - Baseline (with surge/critical detection)
    
    All outputs normalized 0-100
    """

    def __init__(self):
        self.flood_baseline_w = settings.FLOOD_BASELINE_WEIGHTS
        self.flood_event_w = settings.FLOOD_EVENT_WEIGHTS
        self.heat_event_w = settings.HEAT_EVENT_WEIGHTS

    @staticmethod
    def normalize(value: float, min_val: float, max_val: float) -> float:
        """Normalize value to 0-1 range"""
        if max_val <= min_val:
            return 0.5
        return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))

    # --- FLOOD BASELINE ---

    def calculate_historical_frequency_score(self, ward, all_wards: list) -> float:
        """Score based on historical flood frequency relative to other wards"""
        frequencies = [w.historical_flood_frequency or 0 for w in all_wards]
        max_freq = max(frequencies) if frequencies else 1
        min_freq = min(frequencies) if frequencies else 0
        ward_freq = ward.historical_flood_frequency or 0
        return self.normalize(ward_freq, min_freq, max_freq)

    def calculate_elevation_vulnerability(self, ward) -> float:
        """Lower elevation = higher vulnerability (inverse relationship)"""
        elevation = ward.elevation_m
        if elevation is None or elevation <= 0:
            return 0.5  # Unknown, default to moderate

        # Pune elevation range: ~530m to ~680m
        # Lower elevations are more flood-prone
        return self.normalize(680 - elevation, 0, 150)

    def calculate_drainage_weakness(self, ward) -> float:
        """Drainage weakness = 1 - drainage_index"""
        drainage = ward.drainage_index
        if drainage is None:
            # Estimate from impervious surface
            impervious = ward.impervious_surface_pct
            if impervious is not None:
                return impervious / 100.0
            return 0.5
        return 1.0 - drainage

    def calculate_flood_baseline(self, ward, all_wards: list) -> float:
        """
        Flood Baseline = 0.50*Historical + 0.30*Elevation + 0.20*(1-Drainage)
        Returns: 0-100
        """
        historical = self.calculate_historical_frequency_score(ward, all_wards)
        elevation = self.calculate_elevation_vulnerability(ward)
        drainage = self.calculate_drainage_weakness(ward)

        w = self.flood_baseline_w
        raw = (
            w["historical_frequency"] * historical +
            w["elevation_vulnerability"] * elevation +
            w["drainage_weakness"] * drainage
        )

        return round(min(100, max(0, raw * 100)), 2)

    # --- HEAT BASELINE ---

    def calculate_heatwave_baseline(self, ward, all_wards: list) -> float:
        """
        Heatwave baseline from historical heatwave days + demographics
        Returns: 0-100
        """
        hw_days = [w.historical_heatwave_days or 0 for w in all_wards]
        max_days = max(hw_days) if hw_days else 1
        min_days = min(hw_days) if hw_days else 0

        # Historical component
        hist_score = self.normalize(ward.historical_heatwave_days or 0, min_days, max_days)

        # Elderly vulnerability
        elderly = min(1.0, (ward.elderly_ratio or 0.1) / 0.25)

        # Population density (urban heat island effect)
        density = min(1.0, (ward.population_density or 10000) / 35000)

        raw = 0.50 * hist_score + 0.30 * elderly + 0.20 * density
        return round(min(100, max(0, raw * 100)), 2)

    # --- FLOOD EVENT RISK ---

    def calculate_rainfall_intensity_score(self, rainfall_mm: float) -> float:
        """Score rainfall intensity on 0-1 scale"""
        if rainfall_mm is None:
            return 0.0
        if rainfall_mm < 2:
            return 0.0
        elif rainfall_mm < 20:
            return self.normalize(rainfall_mm, 2, 20) * 0.3
        elif rainfall_mm < 50:
            return 0.3 + self.normalize(rainfall_mm, 20, 50) * 0.3
        elif rainfall_mm < 100:
            return 0.6 + self.normalize(rainfall_mm, 50, 100) * 0.2
        else:
            return min(1.0, 0.8 + self.normalize(rainfall_mm, 100, 200) * 0.2)

    def calculate_cumulative_rain_score(self, cumulative_48h_mm: float) -> float:
        """Score 48-hour cumulative rainfall"""
        if cumulative_48h_mm is None:
            return 0.0
        if cumulative_48h_mm < 10:
            return 0.0
        elif cumulative_48h_mm < 50:
            return self.normalize(cumulative_48h_mm, 10, 50) * 0.3
        elif cumulative_48h_mm < 150:
            return 0.3 + self.normalize(cumulative_48h_mm, 50, 150) * 0.4
        elif cumulative_48h_mm < 300:
            return 0.7 + self.normalize(cumulative_48h_mm, 150, 300) * 0.2
        else:
            return min(1.0, 0.9 + self.normalize(cumulative_48h_mm, 300, 500) * 0.1)

    def calculate_flood_event_risk(self, ward, weather_data: Optional[Dict] = None,
                                     baseline_vulnerability: float = 0.5) -> Dict:
        """
        Flood Event = 0.60*Forecast + 0.20*Cumulative48h + 0.20*Baseline
        Returns: dict with event_risk, factors, weather info
        """
        factors = {}

        if weather_data:
            forecast = weather_data.get("forecast", {})
            current = weather_data.get("current", {})

            rainfall_mm = current.get("rainfall_mm", 0) or 0
            cumulative_48h = forecast.get("rainfall_48h_mm", 0) or 0
            max_intensity = forecast.get("max_rainfall_intensity_mm_h", 0) or 0

            # Use max of current and max intensity
            effective_rainfall = max(rainfall_mm, max_intensity)

            rainfall_score = self.calculate_rainfall_intensity_score(effective_rainfall)
            cumulative_score = self.calculate_cumulative_rain_score(cumulative_48h)

            factors["rainfall_intensity"] = round(rainfall_score, 4)
            factors["cumulative_48h"] = round(cumulative_score, 4)
            factors["baseline_vulnerability"] = round(baseline_vulnerability, 4)
        else:
            rainfall_score = 0.0
            cumulative_score = 0.0
            effective_rainfall = 0.0
            cumulative_48h = 0.0
            factors["rainfall_intensity"] = 0.0
            factors["cumulative_48h"] = 0.0
            factors["baseline_vulnerability"] = round(baseline_vulnerability, 4)

        w = self.flood_event_w
        raw = (
            w["forecast_rainfall_intensity"] * rainfall_score +
            w["cumulative_rain_48h"] * cumulative_score +
            w["baseline_vulnerability"] * baseline_vulnerability
        )

        event_risk = round(min(100, max(0, raw * 100)), 2)

        return {
            "event_risk": event_risk,
            "factors": factors,
            "current_rainfall_mm": effective_rainfall if weather_data else None,
            "rainfall_forecast_48h_mm": cumulative_48h if weather_data else None,
        }

    # --- HEAT EVENT RISK ---

    def calculate_temp_anomaly_score(self, anomaly_c: float) -> float:
        """Score temperature anomaly on 0-1 scale.

        Calibrated so that normal daytime fluctuations (0-3 °C above daily
        average baseline) barely register, while genuine heatwave conditions
        (>5 °C above average) score highly.
        """
        if anomaly_c is None or anomaly_c < 0:
            return 0.0
        if anomaly_c < 3:
            # Normal daytime variation — very low score
            return anomaly_c / 3 * 0.10
        elif anomaly_c < 5:
            # Notable — moderate concern
            return 0.10 + (anomaly_c - 3) / 2 * 0.25
        elif anomaly_c < 8:
            # Significant — watch / warn
            return 0.35 + (anomaly_c - 5) / 3 * 0.35
        else:
            # Extreme heatwave
            return min(1.0, 0.70 + (anomaly_c - 8) / 4 * 0.30)

    def calculate_heat_event_risk(self, ward, weather_data: Optional[Dict] = None,
                                    baseline_vulnerability: float = 0.5) -> Dict:
        """
        Heat Event = 0.55*TempAnomaly + 0.20*BaselineVulnerability + 0.25*UHI
        
        The UHI (Urban Heat Island) factor differentiates wards even when
        they share identical temperature anomalies by using ward-specific
        characteristics (impervious surface %, population density, elderly ratio).
        Returns: dict with event_risk, factors, weather info
        """
        factors = {}

        if weather_data:
            current = weather_data.get("current", {})
            forecast = weather_data.get("forecast", {})

            current_temp = current.get("temperature_c")
            avg_forecast_temp = forecast.get("avg_temp_forecast_c")
            baseline_temp = ward.baseline_avg_temp_c or 28.0

            # Anomaly = current vs historical average
            effective_temp = current_temp or avg_forecast_temp or baseline_temp
            anomaly = effective_temp - baseline_temp

            anomaly_score = self.calculate_temp_anomaly_score(anomaly)

            factors["temperature_anomaly"] = round(anomaly_score, 4)
            factors["baseline_vulnerability"] = round(baseline_vulnerability, 4)
        else:
            anomaly = 0.0
            anomaly_score = 0.0
            effective_temp = ward.baseline_avg_temp_c or 28.0
            factors["temperature_anomaly"] = 0.0
            factors["baseline_vulnerability"] = round(baseline_vulnerability, 4)

        # --- Urban Heat Island (UHI) modifier ---
        # Creates per-ward differentiation even when temp anomaly is uniform
        impervious = (ward.impervious_surface_pct or 50) / 100
        density_norm = min(1.0, (ward.population_density or 10000) / 35000)
        elderly_norm = min(1.0, (ward.elderly_ratio or 0.10) / 0.20)
        drainage = ward.drainage_index or 0.5

        uhi_score = (
            0.35 * impervious +          # heat absorption surfaces
            0.25 * density_norm +         # urban density
            0.20 * elderly_norm +         # demographic vulnerability
            0.20 * (1 - drainage)         # poor infrastructure proxy
        )
        uhi_score = max(0.0, min(1.0, uhi_score))
        factors["urban_heat_island"] = round(uhi_score, 4)

        # Revised weights: anomaly 55%, baseline 20%, UHI 25%
        raw = (
            0.55 * anomaly_score +
            0.20 * baseline_vulnerability +
            0.25 * uhi_score
        )

        event_risk = round(min(100, max(0, raw * 100)), 2)

        return {
            "event_risk": event_risk,
            "factors": factors,
            "current_temp_c": effective_temp if weather_data else None,
            "temp_anomaly_c": round(anomaly, 2) if weather_data else None,
        }

    # --- RISK DELTA ---

    def calculate_risk_delta(self, event_risk: float, baseline_risk: float) -> Dict:
        """
        Risk Delta = Event - Baseline
        With surge and critical alert detection
        """
        delta = event_risk - baseline_risk
        delta_pct = (delta / baseline_risk * 100) if baseline_risk > 0 else 0

        # Only trigger alerts on risk INCREASES (positive delta), not decreases
        surge_alert = delta_pct >= settings.DELTA_SURGE_THRESHOLD
        critical_alert = delta_pct >= settings.DELTA_CRITICAL_THRESHOLD

        if delta_pct >= settings.DELTA_CRITICAL_THRESHOLD:
            surge_level = "critical"
        elif delta_pct >= settings.DELTA_SURGE_THRESHOLD:
            surge_level = "surge"
        elif delta_pct >= 10:
            surge_level = "elevated"
        elif delta_pct <= -10:
            surge_level = "decreasing"
        else:
            surge_level = "stable"

        return {
            "delta": round(delta, 2),
            "delta_pct": round(delta_pct, 2),
            "surge_level": surge_level,
            "surge_alert": surge_alert,
            "critical_alert": critical_alert,
        }

    # --- RISK CATEGORIES ---

    @staticmethod
    def get_risk_category(score: float) -> str:
        """Get risk category from score (0-100)"""
        if score >= settings.RISK_HIGH_THRESHOLD:
            return "critical"
        elif score >= settings.RISK_MODERATE_THRESHOLD:
            return "high"
        elif score >= settings.RISK_LOW_THRESHOLD:
            return "moderate"
        return "low"
