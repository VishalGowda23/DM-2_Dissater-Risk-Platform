"""
Resource Allocation Optimizer
Proportional constrained allocation with critical ward override
"""
from typing import Dict, List, Optional, Any
import math
import logging

from app.db.config import settings

logger = logging.getLogger(__name__)


# Default resource types with deployment configs
DEFAULT_RESOURCES = {
    "water_pumps": {
        "name": "Water Pumps",
        "total": 50,
        "unit": "units",
        "min_per_ward": 0,
        "min_for_critical": 2,
        "effectiveness": {"flood": 0.9, "heat": 0.0},
    },
    "evacuation_buses": {
        "name": "Evacuation Buses",
        "total": 30,
        "unit": "buses",
        "min_per_ward": 0,
        "min_for_critical": 1,
        "effectiveness": {"flood": 0.7, "heat": 0.3},
    },
    "relief_camps": {
        "name": "Relief Camps",
        "total": 20,
        "unit": "camps",
        "min_per_ward": 0,
        "min_for_critical": 1,
        "effectiveness": {"flood": 0.6, "heat": 0.6},
    },
    "cooling_centers": {
        "name": "Cooling Centers",
        "total": 25,
        "unit": "centers",
        "min_per_ward": 0,
        "min_for_critical": 1,
        "effectiveness": {"flood": 0.0, "heat": 0.9},
    },
    "medical_units": {
        "name": "Mobile Medical Units",
        "total": 15,
        "unit": "units",
        "min_per_ward": 0,
        "min_for_critical": 1,
        "effectiveness": {"flood": 0.5, "heat": 0.7},
    },
}


class ResourceAllocator:
    """
    Proportional constrained resource allocation
    
    Need = Risk × Population
    Allocation = Total × (Need / Sum(Need))
    
    With:
    - Minimum allocation threshold for critical wards
    - Critical ward override (risk > 80)
    - Largest Remainder rounding for integer allocations
    - Per-resource optimization
    """

    def calculate_need_score(self, ward_risk: Dict, use_delta: bool = False) -> float:
        """
        Calculate ward need score
        Need = Risk × Population (with optional delta boost)
        """
        risk = ward_risk.get("final_combined_risk", 0) or 0
        population = ward_risk.get("population", 100000) or 100000

        base_need = (risk / 100) * population

        # Boost for surge conditions
        if use_delta:
            flood_delta = abs(ward_risk.get("flood_risk_delta_pct", 0) or 0)
            heat_delta = abs(ward_risk.get("heat_risk_delta_pct", 0) or 0)
            max_delta = max(flood_delta, heat_delta)

            if max_delta > 40:
                base_need *= 1.5  # Critical surge
            elif max_delta > 20:
                base_need *= 1.2  # Surge

        return base_need

    def allocate_resource(self, wards_needs: List[Dict], total_available: int,
                           min_for_critical: int = 1) -> List[Dict]:
        """
        Proportional allocation with Largest Remainder rounding
        
        Args:
            wards_needs: list of {ward_id, need_score, risk_category, ...}
            total_available: total units to distribute
            min_for_critical: minimum units for critical wards
        
        Returns: list of {ward_id, allocated, need_score, ...}
        """
        if not wards_needs or total_available <= 0:
            return []

        total_need = sum(w["need_score"] for w in wards_needs)
        if total_need <= 0:
            # Equal distribution
            per_ward = total_available // len(wards_needs)
            return [{**w, "allocated": per_ward} for w in wards_needs]

        # Step 1: Ensure minimum for critical wards
        critical_wards = [w for w in wards_needs if w.get("risk_category") in ["critical", "high"]]
        guaranteed = len(critical_wards) * min_for_critical
        remaining = max(0, total_available - guaranteed)

        # Step 2: Proportional allocation of remaining
        allocations = []
        for w in wards_needs:
            proportion = w["need_score"] / total_need
            ideal = remaining * proportion

            is_critical = w.get("risk_category") in ["critical", "high"]
            guaranteed_units = min_for_critical if is_critical else 0

            allocations.append({
                **w,
                "ideal": ideal + guaranteed_units,
                "floor": math.floor(ideal) + guaranteed_units,
                "remainder": (ideal + guaranteed_units) - math.floor(ideal) - guaranteed_units,
                "allocated": 0,
            })

        # Step 3: Largest Remainder rounding
        total_floor = sum(a["floor"] for a in allocations)
        leftover = total_available - total_floor

        # Sort by remainder descending
        sorted_alloc = sorted(allocations, key=lambda x: x["remainder"], reverse=True)
        for i in range(min(leftover, len(sorted_alloc))):
            sorted_alloc[i]["floor"] += 1

        # Set final allocations
        for a in allocations:
            a["allocated"] = max(0, a["floor"])
            # Cleanup temp fields
            del a["ideal"]
            del a["floor"]
            del a["remainder"]

        return allocations

    def optimize_allocation(self, ward_risk_data: List[Dict],
                              resources: Dict = None,
                              use_delta: bool = True) -> Dict:
        """
        Full optimization across all resource types
        
        Args:
            ward_risk_data: list of ward risk score dicts
            resources: custom resource config (or use defaults)
            use_delta: whether to boost allocation for surge wards
        
        Returns: complete allocation plan
        """
        resources = resources or DEFAULT_RESOURCES

        # Calculate need scores
        for ward in ward_risk_data:
            ward["need_score"] = self.calculate_need_score(ward, use_delta)

        allocations = {}
        total_allocated = 0

        for resource_key, resource_config in resources.items():
            total = resource_config["total"]
            min_crit = resource_config.get("min_for_critical", settings.MIN_ALLOCATION_CRITICAL_WARD)

            # Resource-specific scoring adjustment
            effectiveness = resource_config.get("effectiveness", {})
            adjusted_wards = self._adjust_for_effectiveness(ward_risk_data, effectiveness)

            # Allocate
            result = self.allocate_resource(adjusted_wards, total, min_crit)

            allocations[resource_key] = {
                "resource_name": resource_config["name"],
                "total_available": total,
                "unit": resource_config["unit"],
                "ward_allocations": self._format_allocations(result),
                "total_allocated": sum(w["allocated"] for w in result),
            }
            total_allocated += allocations[resource_key]["total_allocated"]

        # Generate explanations
        explanations = self._generate_explanations(ward_risk_data, allocations)

        return {
            "allocations": allocations,
            "summary": {
                "total_wards": len(ward_risk_data),
                "total_resources_types": len(resources),
                "total_units_allocated": total_allocated,
                "critical_wards": sum(1 for w in ward_risk_data if w.get("risk_category") in ["critical", "high"]),
                "surge_wards": sum(1 for w in ward_risk_data if w.get("surge_alert")),
                "use_delta": use_delta,
            },
            "explanations": explanations,
        }

    def _adjust_for_effectiveness(self, wards: List[Dict], effectiveness: Dict) -> List[Dict]:
        """Adjust need scores based on resource effectiveness per hazard"""
        adjusted = []
        for w in wards:
            ward_copy = dict(w)

            # Blend effectiveness based on ward's primary hazard
            top_hazard = w.get("top_hazard", "flood")
            eff = effectiveness.get(top_hazard, 0.5)

            if eff < 0.1:
                # This resource isn't useful for this hazard type
                ward_copy["need_score"] *= 0.1
            else:
                ward_copy["need_score"] *= eff

            adjusted.append(ward_copy)

        return adjusted

    def _format_allocations(self, allocations: List[Dict]) -> List[Dict]:
        """Format ward allocations for API response"""
        return [
            {
                "ward_id": a["ward_id"],
                "ward_name": a.get("ward_name", ""),
                "allocated": a["allocated"],
                "need_score": round(a["need_score"], 2),
                "risk_category": a.get("risk_category", "unknown"),
            }
            for a in sorted(allocations, key=lambda x: x["allocated"], reverse=True)
        ]

    def _generate_explanations(self, wards: List[Dict], allocations: Dict) -> List[str]:
        """Generate human-readable allocation explanations"""
        explanations = []

        critical = [w for w in wards if w.get("risk_category") in ["critical", "high"]]
        if critical:
            names = ", ".join(w.get("ward_name", w["ward_id"]) for w in critical[:5])
            explanations.append(
                f"Priority allocation to {len(critical)} high/critical risk wards: {names}"
            )

        surge = [w for w in wards if w.get("surge_alert")]
        if surge:
            explanations.append(
                f"{len(surge)} wards experiencing risk surge — additional resources allocated"
            )

        for key, alloc in allocations.items():
            total = alloc["total_allocated"]
            available = alloc["total_available"]
            explanations.append(
                f"{alloc['resource_name']}: {total}/{available} {alloc['unit']} allocated across {len(alloc['ward_allocations'])} wards"
            )

        return explanations


# Global instance
resource_allocator = ResourceAllocator()
