"""
Cascading Risk Engine
Models compound event chains where multiple hazards amplify each other.
E.g., cloudburst + dam release + blocked drains = catastrophic compound event.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
import logging
import math

from app.services.risk_engine.composite import CompositeRiskCalculator

logger = logging.getLogger(__name__)


@dataclass
class CascadeChain:
    """A cascade chain describes how one event triggers another"""
    chain_id: str
    name: str
    description: str
    trigger: str            # Initial event
    stages: List[Dict]      # [{event, delay_hours, amplification, description}]
    final_multiplier: float # How much the overall risk is amplified
    affected_hazards: List[str]  # flood, heat, or both
    probability: str        # low, medium, high


# Pune-specific cascading event chains
CASCADE_CHAINS = {
    "dam_flood": CascadeChain(
        chain_id="dam_flood",
        name="Dam Release Cascade",
        description="Heavy rainfall → Khadakwasla dam level rise → emergency release → "
                    "downstream ward flooding within 4 hours",
        trigger="Rainfall > 100mm in 24h in catchment area",
        stages=[
            {
                "event": "Heavy rainfall in catchment",
                "delay_hours": 0,
                "amplification": 1.0,
                "description": "Intense rainfall begins filling Khadakwasla reservoir",
                "icon": "🌧️",
            },
            {
                "event": "Reservoir level reaches 90%",
                "delay_hours": 6,
                "amplification": 1.2,
                "description": "Dam authorities monitor rising levels, issue preliminary alert",
                "icon": "🏞️",
            },
            {
                "event": "Emergency discharge begins",
                "delay_hours": 10,
                "amplification": 1.5,
                "description": "25,000+ cusec release into Mutha river toward Pune city",
                "icon": "💧",
            },
            {
                "event": "Downstream ward flooding",
                "delay_hours": 14,
                "amplification": 2.2,
                "description": "River overflows banks at Vithalwadi, Sangam. Waters enter Kasba Peth, Sahakarnagar",
                "icon": "🌊",
            },
        ],
        final_multiplier=2.2,
        affected_hazards=["flood"],
        probability="high",
    ),
    "power_heat": CascadeChain(
        chain_id="power_heat",
        name="Heatwave Power Grid Cascade",
        description="Extreme heat → AC demand spike → grid overload → power outage → "
                    "cooling loss → heat stroke surge in elderly",
        trigger="Temperature > 42°C for 3+ days",
        stages=[
            {
                "event": "Sustained extreme temperatures",
                "delay_hours": 0,
                "amplification": 1.0,
                "description": "Temperatures exceed 42°C across Pune for multiple days",
                "icon": "🌡️",
            },
            {
                "event": "Peak power demand surge",
                "delay_hours": 8,
                "amplification": 1.3,
                "description": "AC usage spikes power demand 40% above normal. Grid stress alerts.",
                "icon": "⚡",
            },
            {
                "event": "Localized power outages",
                "delay_hours": 16,
                "amplification": 1.6,
                "description": "Transformer failures in dense wards. 50,000+ without power.",
                "icon": "🔌",
            },
            {
                "event": "Hospital heat stroke surge",
                "delay_hours": 24,
                "amplification": 2.0,
                "description": "250%+ increase in heat exhaustion/stroke cases at hospitals. Elderly most vulnerable.",
                "icon": "🏥",
            },
        ],
        final_multiplier=2.0,
        affected_hazards=["heat"],
        probability="medium",
    ),
    "monsoon_compound": CascadeChain(
        chain_id="monsoon_compound",
        name="Monsoon Compound Disaster",
        description="Heavy rain + blocked drains + high river + traffic gridlock → "
                    "emergency response failure",
        trigger="Rainfall > 80mm/day + drainage < 60% capacity",
        stages=[
            {
                "event": "Heavy monsoon rainfall begins",
                "delay_hours": 0,
                "amplification": 1.0,
                "description": "Continuous heavy rainfall with 80mm+ in first 12 hours",
                "icon": "🌧️",
            },
            {
                "event": "Storm drains overflow",
                "delay_hours": 4,
                "amplification": 1.4,
                "description": "Clogged/undersized drains overflow. Low-lying roads waterlogged.",
                "icon": "🚰",
            },
            {
                "event": "Major road closures",
                "delay_hours": 8,
                "amplification": 1.7,
                "description": "NH4, Sinhagad Road, Satara Road submerged. Traffic at standstill.",
                "icon": "🚗",
            },
            {
                "event": "Emergency response gridlock",
                "delay_hours": 12,
                "amplification": 2.5,
                "description": "Fire brigade, NDRF, ambulances unable to reach affected areas. "
                               "Rescue boats needed.",
                "icon": "🚨",
            },
        ],
        final_multiplier=2.5,
        affected_hazards=["flood"],
        probability="high",
    ),
    "landslide_flood": CascadeChain(
        chain_id="landslide_flood",
        name="Rain-Triggered Landslide + Flood",
        description="Saturated soil on hills → landslide → debris blocks nallah → "
                    "sudden water surge in downstream wards",
        trigger="7-day cumulative rainfall > 300mm on hilly terrain",
        stages=[
            {
                "event": "Prolonged saturation of hill slopes",
                "delay_hours": 0,
                "amplification": 1.0,
                "description": "Week of continuous rain saturates soil in Sinhagad, Katraj hills",
                "icon": "⛰️",
            },
            {
                "event": "Slope failure / landslide",
                "delay_hours": 2,
                "amplification": 1.3,
                "description": "Earth and debris slide blocks Ambil Odha / Katraj nallah",
                "icon": "🪨",
            },
            {
                "event": "Temporary dam formation",
                "delay_hours": 4,
                "amplification": 1.8,
                "description": "Water pools behind debris. Pressure builds rapidly.",
                "icon": "🏗️",
            },
            {
                "event": "Dam burst — flash flood",
                "delay_hours": 6,
                "amplification": 3.0,
                "description": "Debris dam breaks. Wall of water rushes into downstream wards with no warning.",
                "icon": "⚠️",
            },
        ],
        final_multiplier=3.0,
        affected_hazards=["flood"],
        probability="low",
    ),
}


class CascadingRiskEngine:
    """Evaluate and model cascading/compound disaster scenarios"""

    def __init__(self):
        self.composite = CompositeRiskCalculator()

    def get_chains(self) -> List[Dict]:
        """Return all defined cascade chains"""
        return [asdict(chain) for chain in CASCADE_CHAINS.values()]

    def evaluate_cascade_risk(
        self, chain_id: str, ward, weather_data: Optional[Dict] = None,
        baseline_flood: float = 50.0, baseline_heat: float = 50.0
    ) -> Dict:
        """
        Evaluate a specific cascade chain for a ward.
        Returns the amplified risk and timeline of escalation.
        """
        if chain_id not in CASCADE_CHAINS:
            raise ValueError(f"Unknown cascade chain: {chain_id}")

        chain = CASCADE_CHAINS[chain_id]
        
        # Check trigger conditions
        trigger_met = self._check_trigger(chain, weather_data)
        
        # Calculate base risk
        base_risk = baseline_flood if "flood" in chain.affected_hazards else baseline_heat
        
        # Apply cascade amplification at each stage
        stage_risks = []
        current_risk = base_risk
        
        for stage in chain.stages:
            current_risk = min(100, base_risk * stage["amplification"])
            stage_risks.append({
                **stage,
                "risk_at_stage": round(current_risk, 2),
                "risk_category": self.composite.get_risk_category(current_risk),
            })
        
        # Final amplified risk
        final_risk = min(100, base_risk * chain.final_multiplier)
        
        return {
            "chain": asdict(chain),
            "ward_id": ward.ward_id,
            "ward_name": ward.name,
            "trigger_met": trigger_met,
            "base_risk": round(base_risk, 2),
            "final_risk": round(final_risk, 2),
            "amplification": chain.final_multiplier,
            "risk_increase": round(final_risk - base_risk, 2),
            "stage_timeline": stage_risks,
            "risk_category": self.composite.get_risk_category(final_risk),
        }

    def evaluate_all_cascades(
        self, wards, weather_data_map: Dict = None
    ) -> Dict:
        """Evaluate all cascade chains across all wards"""
        all_wards = list(wards)
        results = {}
        
        for chain_id, chain in CASCADE_CHAINS.items():
            chain_results = []
            for ward in all_wards:
                baseline_flood = self.composite.calculate_flood_baseline(ward, all_wards)
                baseline_heat = self.composite.calculate_heatwave_baseline(ward, all_wards)
                
                ward_weather = weather_data_map.get(ward.ward_id) if weather_data_map else None
                
                result = self.evaluate_cascade_risk(
                    chain_id, ward, ward_weather, baseline_flood, baseline_heat
                )
                chain_results.append(result)
            
            chain_results.sort(key=lambda r: r["final_risk"], reverse=True)
            results[chain_id] = {
                "chain": asdict(chain),
                "ward_results": chain_results,
                "max_risk": chain_results[0]["final_risk"] if chain_results else 0,
                "wards_critical": sum(
                    1 for r in chain_results if r["risk_category"] in ["critical", "high"]
                ),
            }
        
        return {
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "cascades": results,
            "highest_risk_chain": max(
                results.items(), key=lambda x: x[1]["max_risk"]
            )[0] if results else None,
        }

    def _check_trigger(self, chain: CascadeChain, weather_data: Optional[Dict]) -> bool:
        """Check if trigger conditions for a cascade are met"""
        if not weather_data:
            return False
            
        forecast = weather_data.get("forecast", {})
        current = weather_data.get("current", {})
        
        if chain.chain_id == "dam_flood":
            return (forecast.get("rainfall_48h_mm", 0) or 0) > 100
        elif chain.chain_id == "power_heat":
            return (current.get("temperature_c", 0) or 0) > 42
        elif chain.chain_id == "monsoon_compound":
            return (forecast.get("rainfall_48h_mm", 0) or 0) > 80
        elif chain.chain_id == "landslide_flood":
            return (forecast.get("rainfall_7d_mm", 0) or 0) > 300
        
        return False


# Global instance
cascading_engine = CascadingRiskEngine()
