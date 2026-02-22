"""
Final Risk Fusion: Combines Layer 1 (Composite) + Layer 2 (ML)
Includes neighbor spillover, confidence scoring, and alerts
"""
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
import logging

from app.db.config import settings
from app.db.database import get_ward_adjacency
from app.services.risk_engine.composite import CompositeRiskCalculator
from app.ml.model import ml_model
from app.models.ward import Ward, WardRiskScore

logger = logging.getLogger(__name__)


class FinalRiskCalculator:
    """
    Final risk calculation pipeline:
    1. Compute Layer 1 (Composite) risk
    2. Compute Layer 2 (ML) risk  
    3. Fuse: Final = 0.6*Composite + 0.4*ML
    4. Apply neighbor spillover (+5% if adjacent high-risk)
    5. Compute confidence + uncertainty
    6. Generate alerts (surge Δ>20%, critical Δ>40%)
    """

    def __init__(self):
        self.composite = CompositeRiskCalculator()
        self.ml = ml_model
        self.composite_weight = settings.ML_COMPOSITE_WEIGHT
        self.ml_weight = settings.ML_MODEL_WEIGHT

    def calculate_full_risk(self, ward: Ward, all_wards: List[Ward],
                             weather_data: Optional[Dict] = None,
                             db: Session = None) -> Dict:
        """
        Full risk calculation for a single ward
        Returns complete risk assessment with all layers
        """
        # --- Layer 1: Composite ---
        flood_baseline = self.composite.calculate_flood_baseline(ward, all_wards)
        heat_baseline = self.composite.calculate_heatwave_baseline(ward, all_wards)

        flood_event_result = self.composite.calculate_flood_event_risk(
            ward, weather_data, baseline_vulnerability=flood_baseline / 100
        )
        heat_event_result = self.composite.calculate_heat_event_risk(
            ward, weather_data, baseline_vulnerability=heat_baseline / 100
        )

        flood_event = flood_event_result["event_risk"]
        heat_event = heat_event_result["event_risk"]

        # --- Layer 2: ML Calibration ---
        ml_flood = self.ml.predict_flood(ward, weather_data)
        ml_heat = self.ml.predict_heat(ward, weather_data)

        # --- Fusion ---
        # Final = 0.6*Composite + 0.4*ML*100
        final_flood = (
            self.composite_weight * flood_event +
            self.ml_weight * ml_flood["probability"] * 100
        )
        final_heat = (
            self.composite_weight * heat_event +
            self.ml_weight * ml_heat["probability"] * 100
        )

        final_flood = round(min(100, max(0, final_flood)), 2)
        final_heat = round(min(100, max(0, final_heat)), 2)

        # --- Neighbor Spillover ---
        spillover_applied = False
        spillover_sources = []

        if db is not None:
            neighbors = get_ward_adjacency(db, ward.ward_id)
            for neighbor_id in neighbors:
                # Check if neighbor has high risk (most recent score)
                neighbor_score = db.query(WardRiskScore).filter(
                    WardRiskScore.ward_id == neighbor_id
                ).order_by(WardRiskScore.timestamp.desc()).first()

                if neighbor_score and neighbor_score.final_combined_risk and \
                   neighbor_score.final_combined_risk >= settings.NEIGHBOR_RISK_THRESHOLD:
                    spillover_sources.append(neighbor_id)

            if spillover_sources:
                spillover_pct = settings.NEIGHBOR_SPILLOVER_PCT / 100
                final_flood = min(100, final_flood * (1 + spillover_pct))
                final_heat = min(100, final_heat * (1 + spillover_pct))
                spillover_applied = True

        final_combined = max(final_flood, final_heat)

        # --- Risk Delta ---
        flood_delta = self.composite.calculate_risk_delta(flood_event, flood_baseline)
        heat_delta = self.composite.calculate_risk_delta(heat_event, heat_baseline)

        # --- Confidence & Uncertainty ---
        data_completeness = ward.get_data_completeness() if hasattr(ward, 'get_data_completeness') else 0.5
        ml_confidence = (ml_flood["confidence"] + ml_heat["confidence"]) / 2
        weather_available = 1.0 if weather_data else 0.0

        confidence_score = round(
            0.40 * data_completeness +
            0.30 * ml_confidence +
            0.30 * weather_available, 4
        )
        uncertainty_score = round(1.0 - confidence_score, 4)

        # --- Alerts ---
        surge_alert = flood_delta["surge_alert"] or heat_delta["surge_alert"]
        critical_alert = flood_delta["critical_alert"] or heat_delta["critical_alert"]

        alert_message = None
        if critical_alert:
            alert_message = f"CRITICAL: Risk surge detected (Δ>{settings.DELTA_CRITICAL_THRESHOLD}%). Immediate action required."
        elif surge_alert:
            alert_message = f"SURGE: Risk escalation detected (Δ>{settings.DELTA_SURGE_THRESHOLD}%). Monitor closely."

        # --- Top hazard ---
        if final_flood > final_heat and final_flood > 30:
            top_hazard = "flood"
        elif final_heat > final_flood and final_heat > 30:
            top_hazard = "heat"
        else:
            top_hazard = "none"

        # --- Risk category ---
        risk_category = self.composite.get_risk_category(final_combined)

        # --- Top drivers ---
        top_drivers = self._compute_top_drivers(
            flood_event_result, heat_event_result,
            ml_flood.get("shap_values"), ml_heat.get("shap_values"),
            ward
        )

        # --- Recommendations ---
        recommendations = self._generate_recommendations(
            final_flood, final_heat, risk_category, ward
        )

        return {
            # Baselines
            "flood_baseline_risk": flood_baseline,
            "heat_baseline_risk": heat_baseline,
            # Event risks
            "flood_event_risk": flood_event,
            "heat_event_risk": heat_event,
            # Deltas
            "flood_risk_delta": flood_delta["delta"],
            "flood_risk_delta_pct": flood_delta["delta_pct"],
            "heat_risk_delta": heat_delta["delta"],
            "heat_risk_delta_pct": heat_delta["delta_pct"],
            # ML
            "ml_flood_probability": ml_flood["probability"],
            "ml_heat_probability": ml_heat["probability"],
            "ml_confidence": round(ml_confidence, 4),
            # Final
            "final_flood_risk": final_flood,
            "final_heat_risk": final_heat,
            "final_combined_risk": round(final_combined, 2),
            # Confidence
            "confidence_score": confidence_score,
            "uncertainty_score": uncertainty_score,
            # Spillover
            "neighbor_spillover_applied": spillover_applied,
            "spillover_source_wards": spillover_sources,
            # Weather
            "current_rainfall_mm": flood_event_result.get("current_rainfall_mm"),
            "rainfall_forecast_48h_mm": flood_event_result.get("rainfall_forecast_48h_mm"),
            "current_temp_c": heat_event_result.get("current_temp_c"),
            "temp_anomaly_c": heat_event_result.get("temp_anomaly_c"),
            "weather_condition": weather_data.get("current", {}).get("condition") if weather_data else None,
            "wind_speed_kmh": weather_data.get("current", {}).get("wind_speed_kmh") if weather_data else None,
            "humidity_pct": weather_data.get("current", {}).get("humidity_pct") if weather_data else None,
            "rainfall_forecast_7d_mm": weather_data.get("forecast", {}).get("rainfall_7d_mm") if weather_data else None,
            # Alerts
            "top_hazard": top_hazard,
            "top_risk_score": round(final_combined, 2),
            "risk_category": risk_category,
            "surge_alert": surge_alert,
            "critical_alert": critical_alert,
            "alert_message": alert_message,
            # Explainability
            "risk_factors": {
                "flood_event": flood_event_result.get("factors", {}),
                "heat_event": heat_event_result.get("factors", {}),
            },
            "top_drivers": top_drivers,
            "shap_values": {
                "flood": ml_flood.get("shap_values"),
                "heat": ml_heat.get("shap_values"),
            },
            "recommendations": recommendations,
        }

    def _compute_top_drivers(self, flood_result: Dict, heat_result: Dict,
                               flood_shap: Optional[Dict], heat_shap: Optional[Dict],
                               ward: Ward) -> List[Dict]:
        """Extract top 5 risk-contributing factors"""
        drivers = []

        # From composite factors
        flood_factors = flood_result.get("factors", {})
        heat_factors = heat_result.get("factors", {})

        factor_map = {
            "rainfall_intensity": ("Rainfall intensity", flood_factors.get("rainfall_intensity", 0)),
            "cumulative_48h": ("48h cumulative rainfall", flood_factors.get("cumulative_48h", 0)),
            "baseline_vulnerability": ("Historical vulnerability", max(
                flood_factors.get("baseline_vulnerability", 0),
                heat_factors.get("baseline_vulnerability", 0)
            )),
            "temperature_anomaly": ("Temperature anomaly", heat_factors.get("temperature_anomaly", 0)),
        }

        # Add SHAP-based drivers if available
        if flood_shap:
            for key, val in flood_shap.items():
                if key not in factor_map and abs(val) > 0.01:
                    readable = key.replace("_", " ").title()
                    factor_map[key] = (readable, abs(val))

        # Sort by impact
        sorted_factors = sorted(factor_map.items(), key=lambda x: x[1][1], reverse=True)

        for key, (name, impact) in sorted_factors[:5]:
            drivers.append({
                "factor": key,
                "name": name,
                "impact": round(impact, 4),
                "direction": "increasing" if impact > 0 else "neutral",
            })

        return drivers

    def _generate_recommendations(self, flood_risk: float, heat_risk: float,
                                    category: str, ward: Ward) -> List[str]:
        """Generate actionable recommendations based on risk level"""
        recs = []

        if category == "critical":
            recs.append("Activate emergency response protocols immediately")
            recs.append("Issue public warning for all residents")

        if flood_risk >= 60:
            recs.append("Deploy water pumps to low-lying areas")
            if ward.drainage_index and ward.drainage_index < 0.4:
                recs.append("Clear blocked drainage channels immediately")
            recs.append("Prepare evacuation buses for flood-prone zones")

        if heat_risk >= 60:
            recs.append("Activate cooling centers in the ward")
            if ward.elderly_ratio and ward.elderly_ratio > 0.12:
                recs.append("Deploy health workers for elderly welfare checks")
            recs.append("Ensure water distribution points are operational")

        if category in ["high", "critical"]:
            recs.append("Alert hospitals for potential casualty surge")
            recs.append("Increase monitoring frequency to every 10 minutes")
        elif category == "moderate":
            recs.append("Continue monitoring, assess again in 30 minutes")

        if not recs:
            recs.append("Risk levels within normal range. Maintain standard monitoring.")

        return recs


# Global instance
final_risk_calculator = FinalRiskCalculator()
