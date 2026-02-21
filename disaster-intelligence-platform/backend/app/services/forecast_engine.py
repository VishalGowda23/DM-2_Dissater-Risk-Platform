"""
48-Hour Temporal Forecasting Engine
Computes risk at T+0, T+6, T+12, T+24, T+48h using hourly weather forecast data
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import math

from app.services.risk_engine.composite import CompositeRiskCalculator

logger = logging.getLogger(__name__)


class ForecastEngine:
    """
    Temporal risk forecasting using hourly weather predictions.
    Takes Open-Meteo hourly forecast data and computes risk evolution over 48 hours.
    
    Key outputs:
    - Risk timeline at T+0, T+6, T+12, T+24, T+48h
    - Peak risk window identification
    - Time-to-critical threshold calculation
    - Alert level progression
    """

    FORECAST_HOURS = [0, 3, 6, 9, 12, 18, 24, 30, 36, 42, 48]
    CRITICAL_THRESHOLD = 75.0
    HIGH_THRESHOLD = 60.0

    def __init__(self):
        self.composite = CompositeRiskCalculator()

    def compute_ward_forecast(
        self, ward, weather_data: Optional[Dict],
        all_wards: list, baseline_flood: float = None, baseline_heat: float = None
    ) -> Dict:
        """
        Compute 48-hour risk forecast for a single ward.
        
        Uses hourly precipitation and temperature data to project risk
        at each forecast timestep.
        """
        # Calculate baselines if not provided
        if baseline_flood is None:
            baseline_flood = self.composite.calculate_flood_baseline(ward, all_wards)
        if baseline_heat is None:
            baseline_heat = self.composite.calculate_heatwave_baseline(ward, all_wards)

        hourly_precip = []
        hourly_temp = []
        hourly_humidity = []
        hourly_wind = []

        if weather_data:
            hourly = weather_data.get("hourly", {})
            hourly_precip = hourly.get("precipitation", [])
            hourly_temp = hourly.get("temperature_2m", [])
            hourly_humidity = hourly.get("humidity", [])
            hourly_wind = hourly.get("wind_speed", [])

        timeline = []
        peak_risk = 0
        peak_hour = 0
        time_to_critical = None

        for hour in self.FORECAST_HOURS:
            # Build synthetic weather snapshot for this hour
            snapshot_weather = self._build_weather_snapshot(
                hour, hourly_precip, hourly_temp, hourly_humidity, hourly_wind
            )

            # Calculate flood event risk with this snapshot
            flood_result = self.composite.calculate_flood_event_risk(
                ward, snapshot_weather,
                baseline_vulnerability=baseline_flood / 100
            )
            flood_risk = flood_result["event_risk"]

            # Calculate heat event risk
            heat_result = self.composite.calculate_heat_event_risk(
                ward, snapshot_weather,
                baseline_vulnerability=baseline_heat / 100
            )
            heat_risk = heat_result["event_risk"]

            combined = max(flood_risk, heat_risk)
            alert_level = self._get_alert_level(combined)

            # Track peak
            if combined > peak_risk:
                peak_risk = combined
                peak_hour = hour

            # Track time-to-critical
            if time_to_critical is None and combined >= self.CRITICAL_THRESHOLD:
                time_to_critical = hour

            timeline.append({
                "hour": hour,
                "timestamp": (datetime.now() + timedelta(hours=hour)).isoformat(),
                "flood_risk": round(flood_risk, 2),
                "heat_risk": round(heat_risk, 2),
                "combined_risk": round(combined, 2),
                "alert_level": alert_level,
                "rainfall_mm": round(snapshot_weather.get("current", {}).get("rainfall_mm", 0) or 0, 1),
                "temperature_c": round(snapshot_weather.get("current", {}).get("temperature_c", 0) or 0, 1),
            })

        # Determine trend
        if len(timeline) >= 2:
            start_risk = timeline[0]["combined_risk"]
            end_risk = timeline[-1]["combined_risk"]
            if end_risk > start_risk + 5:
                trend = "rising"
            elif end_risk < start_risk - 5:
                trend = "falling"
            else:
                trend = "stable"
        else:
            trend = "unknown"

        return {
            "ward_id": ward.ward_id,
            "ward_name": ward.name,
            "population": ward.population or 0,
            "centroid": {
                "lat": ward.centroid_lat or 0,
                "lon": ward.centroid_lon or 0,
            },
            "baseline": {
                "flood": round(baseline_flood, 2),
                "heat": round(baseline_heat, 2),
            },
            "timeline": timeline,
            "peak": {
                "risk": round(peak_risk, 2),
                "hour": peak_hour,
                "timestamp": (datetime.now() + timedelta(hours=peak_hour)).isoformat(),
                "hazard": "flood" if timeline[self.FORECAST_HOURS.index(peak_hour)]["flood_risk"] > timeline[self.FORECAST_HOURS.index(peak_hour)]["heat_risk"] else "heat",
            },
            "time_to_critical": time_to_critical,
            "trend": trend,
            "current_alert": timeline[0]["alert_level"] if timeline else "normal",
            "max_alert": max(timeline, key=lambda t: t["combined_risk"])["alert_level"] if timeline else "normal",
        }

    def compute_all_wards_forecast(
        self, wards, weather_data_map: Dict[str, Dict] = None
    ) -> Dict:
        """
        Compute 48-hour forecast for all wards.
        Returns sorted by peak risk descending.
        """
        all_wards_list = list(wards)
        weather_data_map = weather_data_map or {}

        forecasts = []
        critical_count = 0
        rising_count = 0

        for ward in all_wards_list:
            ward_weather = weather_data_map.get(ward.ward_id)
            forecast = self.compute_ward_forecast(
                ward, ward_weather, all_wards_list
            )
            forecasts.append(forecast)

            if forecast["time_to_critical"] is not None:
                critical_count += 1
            if forecast["trend"] == "rising":
                rising_count += 1

        # Sort by peak risk descending
        forecasts.sort(key=lambda f: f["peak"]["risk"], reverse=True)

        # Identify danger window (hours where any ward exceeds critical)
        danger_hours = set()
        for f in forecasts:
            for tp in f["timeline"]:
                if tp["combined_risk"] >= self.CRITICAL_THRESHOLD:
                    danger_hours.add(tp["hour"])

        danger_window = None
        if danger_hours:
            danger_window = {
                "start_hour": min(danger_hours),
                "end_hour": max(danger_hours),
                "start_time": (datetime.now() + timedelta(hours=min(danger_hours))).isoformat(),
                "end_time": (datetime.now() + timedelta(hours=max(danger_hours))).isoformat(),
            }

        return {
            "timestamp": datetime.now().isoformat(),
            "forecast_hours": self.FORECAST_HOURS,
            "total_wards": len(forecasts),
            "wards_reaching_critical": critical_count,
            "wards_risk_rising": rising_count,
            "danger_window": danger_window,
            "forecasts": forecasts,
        }

    def _build_weather_snapshot(
        self, hour: int,
        hourly_precip: list, hourly_temp: list,
        hourly_humidity: list, hourly_wind: list
    ) -> Dict:
        """
        Build a weather data snapshot for the composite calculator
        at a specific forecast hour.
        """
        idx = min(hour, len(hourly_precip) - 1) if hourly_precip else -1

        current_rainfall = hourly_precip[idx] if idx >= 0 else 0
        current_temp = hourly_temp[idx] if idx >= 0 and idx < len(hourly_temp) else 28
        current_humidity = hourly_humidity[idx] if idx >= 0 and idx < len(hourly_humidity) else 65
        current_wind = hourly_wind[idx] if idx >= 0 and idx < len(hourly_wind) else 10

        # Cumulative rainfall: sum from now to this hour
        end_for_48h = min(idx + 48, len(hourly_precip)) if hourly_precip else 0
        cumulative_48h = sum(hourly_precip[idx:end_for_48h]) if hourly_precip and idx >= 0 else 0

        # 7-day cumulative (approximate from available data)
        end_for_7d = min(idx + 168, len(hourly_precip)) if hourly_precip else 0
        cumulative_7d = sum(hourly_precip[idx:end_for_7d]) if hourly_precip and idx >= 0 else 0

        # Max intensity in upcoming window
        window_end = min(idx + 24, len(hourly_precip)) if hourly_precip else 0
        max_intensity = max(hourly_precip[idx:window_end]) if hourly_precip and idx >= 0 and window_end > idx else 0

        # Temperature forecast (average of next 3 hours)
        temp_window = hourly_temp[idx:min(idx + 72, len(hourly_temp))] if hourly_temp and idx >= 0 else []
        avg_temp = sum(t for t in temp_window if t is not None) / max(len(temp_window), 1) if temp_window else 28

        return {
            "current": {
                "temperature_c": current_temp,
                "rainfall_mm": current_rainfall,
                "humidity_pct": current_humidity,
                "wind_speed_kmh": current_wind,
                "condition": self._classify_condition(current_rainfall, current_temp, max_intensity),
            },
            "forecast": {
                "rainfall_48h_mm": round(cumulative_48h, 2),
                "rainfall_7d_mm": round(cumulative_7d, 2),
                "max_rainfall_intensity_mm_h": round(max_intensity, 2),
                "avg_temp_forecast_c": round(avg_temp, 1),
            },
        }

    def _classify_condition(self, rainfall: float, temp: float, intensity: float) -> str:
        if intensity > 50:
            return "heavy_rain"
        if intensity > 20:
            return "moderate_rain"
        if rainfall and rainfall > 0.5:
            return "light_rain"
        if temp and temp > 42:
            return "extreme_heat"
        if temp and temp > 38:
            return "heatwave"
        return "clear"

    def _get_alert_level(self, risk: float) -> str:
        if risk >= 80:
            return "emergency"
        if risk >= 65:
            return "warning"
        if risk >= 50:
            return "watch"
        if risk >= 30:
            return "advisory"
        return "normal"


# Global instance
forecast_engine = ForecastEngine()
