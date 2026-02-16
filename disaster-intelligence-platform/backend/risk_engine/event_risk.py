"""
Event risk calculation module
Computes real-time event risk using weather forecast data
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

from models.ward import Ward
from core.config import settings
from ingestion.weather_api import WeatherAPIClient

logger = logging.getLogger(__name__)


class EventRiskCalculator:
    """Calculate event (forecast-driven) risk scores"""
    
    def __init__(self, weather_client: Optional[WeatherAPIClient] = None):
        self.weather_client = weather_client or WeatherAPIClient()
        self.flood_weights = settings.FLOOD_EVENT_WEIGHTS
        self.heat_weights = settings.HEAT_EVENT_WEIGHTS
    
    def normalize(self, value: float, min_val: float, max_val: float) -> float:
        """Normalize value to 0-1 range"""
        if max_val == min_val:
            return 0.5
        normalized = (value - min_val) / (max_val - min_val)
        return max(0.0, min(1.0, normalized))
    
    def calculate_rainfall_intensity_score(self, rainfall_mm: float) -> float:
        """
        Calculate rainfall intensity score
        0-20mm: Low (0-0.3)
        20-50mm: Moderate (0.3-0.6)
        50-100mm: High (0.6-0.8)
        100mm+: Extreme (0.8-1.0)
        """
        if rainfall_mm < 20:
            return self.normalize(rainfall_mm, 0, 20) * 0.3
        elif rainfall_mm < 50:
            return 0.3 + self.normalize(rainfall_mm, 20, 50) * 0.3
        elif rainfall_mm < 100:
            return 0.6 + self.normalize(rainfall_mm, 50, 100) * 0.2
        else:
            return min(1.0, 0.8 + self.normalize(rainfall_mm, 100, 200) * 0.2)
    
    def calculate_cumulative_rain_score(self, cumulative_mm: float) -> float:
        """
        Calculate 48-hour cumulative rain score
        0-50mm: Low
        50-100mm: Moderate
        100-200mm: High
        200mm+: Extreme
        """
        if cumulative_mm < 50:
            return self.normalize(cumulative_mm, 0, 50) * 0.3
        elif cumulative_mm < 100:
            return 0.3 + self.normalize(cumulative_mm, 50, 100) * 0.3
        elif cumulative_mm < 200:
            return 0.6 + self.normalize(cumulative_mm, 100, 200) * 0.2
        else:
            return min(1.0, 0.8 + self.normalize(cumulative_mm, 200, 400) * 0.2)
    
    def calculate_temp_anomaly_score(self, anomaly_c: float) -> float:
        """
        Calculate temperature anomaly score
        0-2C: Normal (0-0.2)
        2-4C: Elevated (0.2-0.5)
        4-6C: High (0.5-0.8)
        6C+: Extreme (0.8-1.0)
        """
        if anomaly_c < 2:
            return self.normalize(anomaly_c, 0, 2) * 0.2
        elif anomaly_c < 4:
            return 0.2 + self.normalize(anomaly_c, 2, 4) * 0.3
        elif anomaly_c < 6:
            return 0.5 + self.normalize(anomaly_c, 4, 6) * 0.3
        else:
            return min(1.0, 0.8 + self.normalize(anomaly_c, 6, 10) * 0.2)
    
    async def calculate_flood_event_risk(
        self, 
        ward: Ward, 
        weather_data: Optional[Dict] = None,
        baseline_vulnerability: float = 0.5
    ) -> Dict:
        """
        Calculate event flood risk for a ward
        Formula: 0.60*Forecast_Rainfall_Intensity + 0.20*48h_Cumulative_Rain + 0.20*Baseline_Vulnerability
        Returns: Risk score and factor breakdown
        """
        try:
            # Fetch weather data if not provided
            if weather_data is None:
                weather_data = await self.weather_client.get_forecast(
                    ward.centroid_lat, 
                    ward.centroid_lon
                )
            
            if not weather_data:
                logger.warning(f"No weather data available for ward {ward.ward_id}")
                return {
                    "event_risk": baseline_vulnerability * 100,
                    "factors": {
                        "rainfall_intensity": {"value": 0, "contribution": 0},
                        "cumulative_rain": {"value": 0, "contribution": 0},
                        "baseline_vulnerability": {"value": baseline_vulnerability, "contribution": baseline_vulnerability * 0.2 * 100},
                    },
                    "data_quality": "fallback"
                }
            
            # Extract rainfall data
            hourly_rain = weather_data.get("hourly", {}).get("rain", [])
            current_rain = hourly_rain[0] if hourly_rain else 0
            
            # Calculate 48-hour cumulative rain
            rain_48h = sum(hourly_rain[:48]) if len(hourly_rain) >= 48 else sum(hourly_rain)
            
            # Calculate factor scores
            rain_intensity = self.calculate_rainfall_intensity_score(current_rain)
            cumulative_score = self.calculate_cumulative_rain_score(rain_48h)
            
            # Weighted sum
            risk = (
                self.flood_weights["forecast_rainfall_intensity"] * rain_intensity +
                self.flood_weights["cumulative_rain_48h"] * cumulative_score +
                self.flood_weights["baseline_vulnerability"] * baseline_vulnerability
            )
            
            return {
                "event_risk": round(risk * 100, 2),
                "current_rainfall_mm": current_rain,
                "rainfall_forecast_48h_mm": rain_48h,
                "factors": {
                    "rainfall_intensity": {
                        "value": round(current_rain, 1),
                        "normalized": round(rain_intensity, 2),
                        "weight": self.flood_weights["forecast_rainfall_intensity"],
                        "contribution": round(rain_intensity * self.flood_weights["forecast_rainfall_intensity"] * 100, 1)
                    },
                    "cumulative_rain": {
                        "value": round(rain_48h, 1),
                        "normalized": round(cumulative_score, 2),
                        "weight": self.flood_weights["cumulative_rain_48h"],
                        "contribution": round(cumulative_score * self.flood_weights["cumulative_rain_48h"] * 100, 1)
                    },
                    "baseline_vulnerability": {
                        "value": round(baseline_vulnerability, 2),
                        "normalized": round(baseline_vulnerability, 2),
                        "weight": self.flood_weights["baseline_vulnerability"],
                        "contribution": round(baseline_vulnerability * self.flood_weights["baseline_vulnerability"] * 100, 1)
                    },
                },
                "data_quality": "live"
            }
            
        except Exception as e:
            logger.error(f"Error calculating flood event risk for ward {ward.ward_id}: {e}")
            return {
                "event_risk": baseline_vulnerability * 100,
                "factors": {},
                "data_quality": "error"
            }
    
    async def calculate_heat_event_risk(
        self, 
        ward: Ward, 
        weather_data: Optional[Dict] = None,
        baseline_vulnerability: float = 0.5
    ) -> Dict:
        """
        Calculate event heatwave risk for a ward
        Formula: 0.70*Temperature_Anomaly + 0.30*Baseline_Vulnerability
        Returns: Risk score and factor breakdown
        """
        try:
            # Fetch weather data if not provided
            if weather_data is None:
                weather_data = await self.weather_client.get_forecast(
                    ward.centroid_lat, 
                    ward.centroid_lon
                )
            
            if not weather_data:
                logger.warning(f"No weather data available for ward {ward.ward_id}")
                return {
                    "event_risk": baseline_vulnerability * 100,
                    "factors": {
                        "temperature_anomaly": {"value": 0, "contribution": 0},
                        "baseline_vulnerability": {"value": baseline_vulnerability, "contribution": baseline_vulnerability * 0.3 * 100},
                    },
                    "data_quality": "fallback"
                }
            
            # Extract temperature data
            hourly_temp = weather_data.get("hourly", {}).get("temperature_2m", [])
            current_temp = hourly_temp[0] if hourly_temp else 30
            
            # Calculate temperature anomaly (difference from seasonal average)
            # Pune average March temperature ~30C
            seasonal_avg = 30.0
            temp_anomaly = max(0, current_temp - seasonal_avg)
            
            # Calculate anomaly score
            anomaly_score = self.calculate_temp_anomaly_score(temp_anomaly)
            
            # Weighted sum
            risk = (
                self.heat_weights["temperature_anomaly"] * anomaly_score +
                self.heat_weights["baseline_vulnerability"] * baseline_vulnerability
            )
            
            return {
                "event_risk": round(risk * 100, 2),
                "current_temp_c": round(current_temp, 1),
                "temp_anomaly_c": round(temp_anomaly, 1),
                "factors": {
                    "temperature_anomaly": {
                        "value": round(temp_anomaly, 1),
                        "normalized": round(anomaly_score, 2),
                        "weight": self.heat_weights["temperature_anomaly"],
                        "contribution": round(anomaly_score * self.heat_weights["temperature_anomaly"] * 100, 1)
                    },
                    "baseline_vulnerability": {
                        "value": round(baseline_vulnerability, 2),
                        "normalized": round(baseline_vulnerability, 2),
                        "weight": self.heat_weights["baseline_vulnerability"],
                        "contribution": round(baseline_vulnerability * self.heat_weights["baseline_vulnerability"] * 100, 1)
                    },
                },
                "data_quality": "live"
            }
            
        except Exception as e:
            logger.error(f"Error calculating heat event risk for ward {ward.ward_id}: {e}")
            return {
                "event_risk": baseline_vulnerability * 100,
                "factors": {},
                "data_quality": "error"
            }
    
    def calculate_risk_delta(self, event_risk: float, baseline_risk: float) -> Dict:
        """Calculate risk delta between event and baseline"""
        delta = event_risk - baseline_risk
        delta_pct = (delta / baseline_risk * 100) if baseline_risk > 0 else 0
        
        # Determine surge level
        surge_level = "normal"
        if delta > settings.DELTA_CRITICAL_THRESHOLD:
            surge_level = "critical"
        elif delta > settings.DELTA_ESCALATION_THRESHOLD:
            surge_level = "escalation"
        
        return {
            "delta": round(delta, 2),
            "delta_pct": round(delta_pct, 1),
            "surge_level": surge_level,
            "escalation_alert": delta > settings.DELTA_ESCALATION_THRESHOLD,
            "critical_surge": delta > settings.DELTA_CRITICAL_THRESHOLD,
        }
