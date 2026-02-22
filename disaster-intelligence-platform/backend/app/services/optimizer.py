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
        Calculate ward need score.
        Risk is primary factor (70%) with population as secondary (30%).
        This ensures high-risk wards get prioritised even if less populated.
        Formula: need = risk_weight^2 * (0.7 + 0.3 * pop_weight)
        """
        risk = ward_risk.get("final_combined_risk", 0) or 0
        population = ward_risk.get("population", 100000) or 100000

        # Normalize population to 0-1 scale (Pune wards: 98K-350K)
        pop_normalized = min(1.0, max(0.0, (population - 50000) / 400000))

        # Risk is primary driver — square it to amplify differences
        risk_weight = (risk / 100) ** 2

        # Combine: 70% risk, 30% population
        base_need = risk_weight * (0.7 + 0.3 * pop_normalized) * 100

        # Boost for active surge conditions (rising risk, not falling)
        if use_delta:
            flood_delta = ward_risk.get("flood_risk_delta_pct", 0) or 0
            heat_delta = ward_risk.get("heat_risk_delta_pct", 0) or 0
            max_delta = max(flood_delta, heat_delta)  # only positive delta = rising risk

            # Only meaningful if absolute risk is also significant
            # A ward at 15→35 (low→moderate) shouldn't outrank a ward at 45 (moderate)
            if max_delta > 0:
                # Scale boost by both delta % and absolute risk level
                risk_gate = min(1.0, risk / 60)  # full factor at risk ≥ 60
                if max_delta > 40:
                    boost = 1.0 + 0.5 * risk_gate  # up to 1.5x at high risk
                elif max_delta > 20:
                    boost = 1.0 + 0.3 * risk_gate  # up to 1.3x
                else:
                    boost = 1.0 + 0.1 * risk_gate  # up to 1.1x
                base_need *= boost

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
            # No ward needs this resource — allocate 0 to all
            return [{**w, "allocated": 0} for w in wards_needs]

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

        # Calculate resource requirements (ideal needed) and gaps
        resource_requirements = self._calculate_resource_requirements(
            ward_risk_data, resources, allocations
        )

        return {
            "allocations": allocations,
            "resource_requirements": resource_requirements,
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

    def _calculate_resource_requirements(self, wards: List[Dict],
                                          resources: Dict,
                                          allocations: Dict) -> Dict:
        """
        Calculate ideal resource requirements per ward and system-wide gaps.
        
        For each resource type, the ideal per-ward need is:
          ideal = ceil(risk_factor * pop_factor * effectiveness)
        where:
          risk_factor = risk / 40 (so risk=40 → 1x, risk=80 → 2x)
          pop_factor  = population / base_pop_per_unit (varies by resource)
          effectiveness = resource effectiveness for ward's top hazard
        
        Gap = max(0, total_required - total_available)
        """
        # Base population per unit for each resource type
        POP_PER_UNIT = {
            "water_pumps": 80000,
            "evacuation_buses": 100000,
            "relief_camps": 150000,
            "cooling_centers": 100000,
            "medical_units": 150000,
        }

        requirements = {}

        for resource_key, resource_config in resources.items():
            effectiveness = resource_config.get("effectiveness", {})
            total_available = resource_config["total"]
            base_pop = POP_PER_UNIT.get(resource_key, 100000)

            ward_requirements = []
            total_required = 0

            for w in wards:
                risk = w.get("final_combined_risk", 0) or 0
                population = w.get("population", 100000) or 100000
                top_hazard = w.get("top_hazard", "flood")

                # If top_hazard is "none" or unknown, determine from actual risk values
                if top_hazard not in effectiveness:
                    flood_risk = w.get("flood_risk", 0) or 0
                    heat_risk = w.get("heat_risk", 0) or 0
                    top_hazard = "heat" if heat_risk > flood_risk else "flood"

                eff = effectiveness.get(top_hazard, 0.0)

                if eff <= 0:
                    # Resource irrelevant for this hazard type
                    ward_requirements.append({
                        "ward_id": w["ward_id"],
                        "required": 0,
                        "allocated": 0,
                        "gap": 0,
                    })
                    continue

                risk_factor = risk / 40.0  # risk 40 = 1x need
                pop_factor = population / base_pop
                ideal = math.ceil(risk_factor * pop_factor * eff)

                # Look up actual allocation for this ward
                actual = 0
                for wa in allocations.get(resource_key, {}).get("ward_allocations", []):
                    if wa["ward_id"] == w["ward_id"]:
                        actual = wa["allocated"]
                        break

                gap = max(0, ideal - actual)
                total_required += ideal

                ward_requirements.append({
                    "ward_id": w["ward_id"],
                    "ward_name": w.get("ward_name", ""),
                    "required": ideal,
                    "allocated": actual,
                    "gap": gap,
                })

            total_gap = max(0, total_required - total_available)
            total_allocated = allocations.get(resource_key, {}).get("total_allocated", 0)

            requirements[resource_key] = {
                "resource_name": resource_config["name"],
                "unit": resource_config["unit"],
                "total_available": total_available,
                "total_required": total_required,
                "total_allocated": total_allocated,
                "total_gap": total_gap,
                "coverage_pct": round(
                    min(100, (total_available / max(total_required, 1)) * 100), 1
                ),
                "ward_requirements": sorted(
                    ward_requirements, key=lambda x: x["gap"], reverse=True
                ),
            }

        return requirements

    def _adjust_for_effectiveness(self, wards: List[Dict], effectiveness: Dict) -> List[Dict]:
        """Adjust need scores based on resource effectiveness per hazard.
        If a resource has 0.0 effectiveness for a hazard (e.g. pumps for heat),
        the ward gets zero allocation for that resource."""
        adjusted = []
        for w in wards:
            ward_copy = dict(w)

            top_hazard = w.get("top_hazard", "flood")

            # If top_hazard is "none" or unknown, determine from actual risk values
            if top_hazard not in effectiveness:
                flood_risk = w.get("flood_risk", 0) or 0
                heat_risk = w.get("heat_risk", 0) or 0
                if heat_risk > flood_risk:
                    top_hazard = "heat"
                elif flood_risk > heat_risk:
                    top_hazard = "flood"
                else:
                    # Both equal or zero — blend effectiveness
                    flood_eff = effectiveness.get("flood", 0.5)
                    heat_eff = effectiveness.get("heat", 0.5)
                    eff = (flood_eff + heat_eff) / 2
                    ward_copy["need_score"] *= eff
                    adjusted.append(ward_copy)
                    continue

            eff = effectiveness.get(top_hazard, 0.0)

            # Zero effectiveness means this resource is irrelevant for this hazard
            # e.g. water_pumps for heat wards = 0, cooling_centers for flood wards = 0
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
