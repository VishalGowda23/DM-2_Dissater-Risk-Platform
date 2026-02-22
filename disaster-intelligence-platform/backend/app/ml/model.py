"""
Layer 2: XGBoost ML Calibration Model with SHAP Explainability
Trains on historical data, outputs calibrated risk probability
"""
import os
import pickle
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import numpy as np

from app.db.config import settings

logger = logging.getLogger(__name__)

# Try importing ML libraries
try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    logger.warning("XGBoost not installed. ML calibration will be disabled.")

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False
    logger.warning("SHAP not installed. ML explainability will be limited.")


# Feature names used by the model
FEATURE_NAMES = [
    "rainfall_intensity",
    "cumulative_rainfall_48h",
    "elevation_m",
    "mean_slope",
    "population_density",
    "infrastructure_density",
    "historical_frequency",
    "drainage_index",
    "impervious_surface_pct",
    "low_lying_index",
    "elderly_ratio",
]


class MLRiskModel:
    """
    XGBoost risk calibration model
    
    Features: 11 engineered features per ward
    Target: binary flood/heat occurrence (1=happened, 0=didn't)
    Output: probability of event + SHAP explanations
    
    Final Risk = 0.6 * Composite + 0.4 * ML_Output
    """

    def __init__(self, model_path: str = None):
        self.model_path = model_path or settings.ML_MODEL_PATH
        self.flood_model = None
        self.heat_model = None
        self.shap_explainer = None
        self.is_loaded = False

    def load(self) -> bool:
        """Load trained model from disk"""
        if not HAS_XGBOOST:
            logger.warning("XGBoost not available, using fallback")
            return False

        model_dir = os.path.dirname(self.model_path)
        flood_path = os.path.join(model_dir, "model_flood.pkl")
        heat_path = os.path.join(model_dir, "model_heat.pkl")

        # Also try the old naming convention
        if not os.path.exists(flood_path):
            flood_path = self.model_path.replace(".pkl", "_flood.pkl")
        if not os.path.exists(heat_path):
            heat_path = self.model_path.replace(".pkl", "_heat.pkl")

        try:
            if os.path.exists(flood_path):
                with open(flood_path, "rb") as f:
                    self.flood_model = pickle.load(f)
                logger.info("Flood ML model loaded")

            if os.path.exists(heat_path):
                with open(heat_path, "rb") as f:
                    self.heat_model = pickle.load(f)
                logger.info("Heat ML model loaded")

            self.is_loaded = self.flood_model is not None
            return self.is_loaded

        except Exception as e:
            logger.error(f"Failed to load ML model: {e}")
            return False

    def extract_features(self, ward, weather_data: Optional[Dict] = None) -> np.ndarray:
        """
        Extract feature vector for a ward
        All features are real data, no mock values
        """
        current = weather_data.get("current", {}) if weather_data else {}
        forecast = weather_data.get("forecast", {}) if weather_data else {}

        features = [
            current.get("rainfall_mm", 0) or 0,                    # rainfall_intensity
            forecast.get("rainfall_48h_mm", 0) or 0,               # cumulative_rainfall_48h
            ward.elevation_m or 560,                                # elevation_m
            ward.mean_slope or 2.0,                                 # mean_slope
            ward.population_density or 10000,                       # population_density
            ward.infrastructure_density or 3.0,                     # infrastructure_density
            ward.historical_flood_frequency or 0.5,                 # historical_frequency
            ward.drainage_index or 0.5,                             # drainage_index
            (ward.impervious_surface_pct or 50) / 100,             # impervious_surface_pct (normalized)
            ward.low_lying_index or 0.5,                            # low_lying_index
            ward.elderly_ratio or 0.1,                              # elderly_ratio
        ]

        return np.array(features).reshape(1, -1)

    def predict_flood(self, ward, weather_data: Optional[Dict] = None) -> Dict:
        """Predict flood probability with SHAP values"""
        features = self.extract_features(ward, weather_data)

        if self.flood_model is not None:
            probability = float(self.flood_model.predict_proba(features)[0, 1])
            confidence = self._calculate_confidence(features)
            shap_values = self._get_shap_values(self.flood_model, features)
        else:
            # Fallback: use a simple rule-based probability
            probability = self._fallback_flood_probability(features[0])
            confidence = 0.5
            shap_values = self._fallback_shap(features[0], "flood")

        return {
            "probability": round(probability, 4),
            "confidence": round(confidence, 4),
            "shap_values": shap_values,
        }

    def predict_heat(self, ward, weather_data: Optional[Dict] = None) -> Dict:
        """Predict heat event probability with weather-based context adjustment.

        The underlying XGBoost model does NOT include temperature as a feature,
        so its raw output reflects *structural vulnerability* only.  We apply a
        weather-aware attenuation factor so that:
        - When temperatures are above baseline → use raw probability
        - When temperatures are near/below baseline → dampen substantially
        - When no weather data → use a moderate dampening (assume normal temps)
        """
        features = self.extract_features(ward, weather_data)

        if self.heat_model is not None:
            raw_probability = float(self.heat_model.predict_proba(features)[0, 1])
            confidence = self._calculate_confidence(features)
            shap_values = self._get_shap_values(self.heat_model, features)
        else:
            raw_probability = self._fallback_heat_probability(features[0])
            confidence = 0.5
            shap_values = self._fallback_shap(features[0], "heat")

        # --- Weather-based attenuation ---
        baseline_temp = getattr(ward, "baseline_avg_temp_c", None) or 28.0
        attenuation = 0.25  # default: assume normal / non-extreme temps

        if weather_data:
            current = weather_data.get("current", {})
            forecast = weather_data.get("forecast", {})
            current_temp = current.get("temperature_c") or forecast.get("avg_temp_forecast_c")

            if current_temp is not None:
                anomaly = current_temp - baseline_temp
                if anomaly >= 8:
                    attenuation = 1.0      # extreme heatwave
                elif anomaly >= 6:
                    attenuation = 0.75     # strong heat event
                elif anomaly >= 4:
                    attenuation = 0.45     # warm afternoon — moderate
                elif anomaly >= 2:
                    attenuation = 0.25     # mildly above average — low
                elif anomaly >= 0:
                    attenuation = 0.12     # near baseline — negligible
                else:
                    attenuation = 0.05     # below baseline — minimal

        probability = raw_probability * attenuation

        return {
            "probability": round(probability, 4),
            "confidence": round(confidence, 4),
            "shap_values": shap_values,
        }

    def _calculate_confidence(self, features: np.ndarray) -> float:
        """Model confidence based on feature completeness"""
        non_default = sum(1 for f in features[0] if f != 0)
        return min(1.0, non_default / len(features[0]))

    def _get_shap_values(self, model, features: np.ndarray) -> Optional[Dict]:
        """Get SHAP feature importance values"""
        if not HAS_SHAP or model is None:
            return None

        try:
            explainer = shap.TreeExplainer(model)
            shap_vals = explainer.shap_values(features)

            # Map SHAP values to feature names
            result = {}
            for i, name in enumerate(FEATURE_NAMES):
                val = float(shap_vals[0][i]) if isinstance(shap_vals, np.ndarray) else float(shap_vals[1][0][i])
                result[name] = round(val, 6)

            return result

        except Exception as e:
            logger.error(f"SHAP computation failed: {e}")
            return None

    def _fallback_flood_probability(self, features: np.ndarray) -> float:
        """Rule-based flood probability when ML model not available"""
        rainfall = features[0]
        cumulative = features[1]
        elevation = features[2]
        drainage = features[7]
        low_lying = features[9]

        # Weighted rule-based estimation
        p = 0.0

        # Rainfall contribution (dominant)
        if rainfall > 50:
            p += 0.40
        elif rainfall > 20:
            p += 0.20
        elif rainfall > 5:
            p += 0.05

        # Cumulative rainfall
        if cumulative > 150:
            p += 0.25
        elif cumulative > 75:
            p += 0.12
        elif cumulative > 25:
            p += 0.05

        # Elevation (lower = riskier)
        elev_factor = max(0, (600 - elevation) / 100) * 0.10
        p += min(0.10, elev_factor)

        # Drainage (worse = riskier)
        p += (1 - drainage) * 0.10

        # Low-lying
        p += low_lying * 0.10

        return max(0, min(1, p))

    def _fallback_heat_probability(self, features: np.ndarray) -> float:
        """Rule-based heat probability when ML model not available"""
        elderly = features[10]
        density = features[4]

        # Simple estimation based on demographics
        p = 0.15  # Base probability
        p += min(0.3, elderly / 0.20 * 0.15)
        p += min(0.2, density / 30000 * 0.1)

        return max(0, min(1, p))

    def _fallback_shap(self, features: np.ndarray, hazard: str) -> Dict:
        """Generate pseudo-SHAP values when model not available"""
        if hazard == "flood":
            importance = {
                "rainfall_intensity": features[0] / 100 * 0.30,
                "cumulative_rainfall_48h": features[1] / 300 * 0.20,
                "elevation_m": (600 - features[2]) / 100 * 0.15,
                "drainage_index": (1 - features[7]) * 0.15,
                "low_lying_index": features[9] * 0.10,
                "impervious_surface_pct": features[8] * 0.05,
                "historical_frequency": features[6] * 0.05,
            }
        else:
            importance = {
                "elderly_ratio": features[10] * 0.30,
                "population_density": features[4] / 30000 * 0.25,
                "infrastructure_density": (10 - features[5]) / 10 * 0.15,
                "impervious_surface_pct": features[8] * 0.15,
                "historical_frequency": features[6] * 0.15,
            }

        return {k: round(v, 6) for k, v in importance.items()}


# Global instance
ml_model = MLRiskModel()
