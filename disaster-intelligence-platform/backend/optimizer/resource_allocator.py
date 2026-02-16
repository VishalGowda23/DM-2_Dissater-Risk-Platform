"""
Resource Allocation Optimizer
Implements constrained proportional allocation algorithm
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

from core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ResourceConstraint:
    """Resource availability constraint"""
    resource_type: str
    total_available: int
    min_per_ward: int = 0
    max_per_ward: Optional[int] = None


@dataclass
class WardNeed:
    """Ward need score for resource allocation"""
    ward_id: str
    ward_name: str
    population: int
    flood_risk: float
    heat_risk: float
    risk_delta: float
    need_score: float


class ResourceAllocator:
    """
    Resource Allocation Optimizer
    
    Algorithm: Proportional Constrained Allocation
    1. Compute Need_Score_w = Risk_w × Population_w
    2. Allocation_w = TotalAvailable × (Need_Score_w / Σ Need_Score)
    3. Round and ensure minimum allocation for critical wards
    """
    
    def __init__(self):
        self.min_allocation_critical = settings.MIN_ALLOCATION_CRITICAL_WARD
        self.critical_threshold = settings.RISK_HIGH_THRESHOLD
    
    def calculate_need_score(
        self, 
        risk: float, 
        population: int, 
        risk_delta: float = 0,
        use_delta: bool = False
    ) -> float:
        """
        Calculate need score for a ward
        
        Args:
            risk: Risk score (0-100)
            population: Ward population
            risk_delta: Risk delta for surge-based allocation
            use_delta: Whether to incorporate risk delta
            
        Returns:
            Need score
        """
        base_score = risk * population / 1000  # Scale by thousands
        
        if use_delta and risk_delta > 0:
            # Boost score for wards with significant risk surge
            surge_multiplier = 1 + (risk_delta / 100)
            base_score *= surge_multiplier
        
        return base_score
    
    def allocate_resource(
        self,
        ward_needs: List[WardNeed],
        constraint: ResourceConstraint,
        use_delta: bool = False
    ) -> Dict[str, Dict]:
        """
        Allocate a single resource type across wards
        
        Args:
            ward_needs: List of ward need scores
            constraint: Resource availability constraint
            use_delta: Whether to use risk delta in allocation
            
        Returns:
            Allocation results per ward
        """
        if not ward_needs or constraint.total_available <= 0:
            return {}
        
        # Calculate total need
        total_need = sum(wn.need_score for wn in ward_needs)
        
        if total_need == 0:
            # Equal distribution if no needs calculated
            per_ward = constraint.total_available // len(ward_needs)
            return {
                wn.ward_id: {
                    "allocated": per_ward,
                    "need_score": wn.need_score,
                    "proportion": 1.0 / len(ward_needs)
                }
                for wn in ward_needs
            }
        
        # Calculate proportional allocations
        allocations = {}
        raw_allocations = {}
        
        for wn in ward_needs:
            proportion = wn.need_score / total_need
            raw_alloc = constraint.total_available * proportion
            raw_allocations[wn.ward_id] = {
                "raw": raw_alloc,
                "proportion": proportion,
                "need_score": wn.need_score
            }
        
        # Round allocations (Largest Remainder Method)
        floor_allocations = {wid: int(data["raw"]) for wid, data in raw_allocations.items()}
        remainders = {wid: data["raw"] - floor_allocations[wid] for wid, data in raw_allocations.items()}
        
        allocated_sum = sum(floor_allocations.values())
        remaining = constraint.total_available - allocated_sum
        
        # Distribute remaining to highest remainders
        sorted_remainders = sorted(remainders.items(), key=lambda x: x[1], reverse=True)
        for i in range(min(remaining, len(sorted_remainders))):
            ward_id = sorted_remainders[i][0]
            floor_allocations[ward_id] += 1
        
        # Ensure minimum for critical wards
        for wn in ward_needs:
            is_critical = wn.flood_risk > self.critical_threshold or wn.heat_risk > self.critical_threshold
            current = floor_allocations.get(wn.ward_id, 0)
            
            if is_critical and current < self.min_allocation_critical:
                # Try to allocate minimum (may need to take from others)
                deficit = self.min_allocation_critical - current
                floor_allocations[wn.ward_id] = self.min_allocation_critical
                
                # Reduce from non-critical wards with highest allocation
                non_critical = [
                    (wid, alloc) for wid, alloc in floor_allocations.items()
                    if wid != wn.ward_id and alloc > self.min_allocation_critical
                ]
                non_critical.sort(key=lambda x: x[1], reverse=True)
                
                for wid, alloc in non_critical:
                    if deficit <= 0:
                        break
                    reduction = min(deficit, alloc - self.min_allocation_critical)
                    floor_allocations[wid] -= reduction
                    deficit -= reduction
        
        # Build final result
        for wn in ward_needs:
            ward_id = wn.ward_id
            allocations[ward_id] = {
                "allocated": floor_allocations.get(ward_id, 0),
                "need_score": raw_allocations[ward_id]["need_score"],
                "proportion": round(raw_allocations[ward_id]["proportion"] * 100, 2),
                "is_critical": wn.flood_risk > self.critical_threshold or wn.heat_risk > self.critical_threshold
            }
        
        return allocations
    
    def optimize_allocation(
        self,
        ward_data: List[Dict],
        resources_available: Dict[str, int],
        scenario_params: Optional[Dict] = None
    ) -> Dict:
        """
        Optimize resource allocation across all wards
        
        Args:
            ward_data: List of ward risk data
            resources_available: Dict of resource_type -> total_available
            scenario_params: Optional scenario parameters
            
        Returns:
            Complete allocation results
        """
        scenario = scenario_params or {}
        use_delta = scenario.get("use_delta", False)
        
        # Build ward needs
        ward_needs = []
        for ward in ward_data:
            top_risk = max(ward.get("flood_risk", 0), ward.get("heat_risk", 0))
            risk_delta = ward.get("risk_delta", 0)
            population = ward.get("population", 1000)
            
            need_score = self.calculate_need_score(
                risk=top_risk,
                population=population,
                risk_delta=risk_delta,
                use_delta=use_delta
            )
            
            ward_needs.append(WardNeed(
                ward_id=ward["ward_id"],
                ward_name=ward.get("ward_name", ward["ward_id"]),
                population=population,
                flood_risk=ward.get("flood_risk", 0),
                heat_risk=ward.get("heat_risk", 0),
                risk_delta=risk_delta,
                need_score=need_score
            ))
        
        # Sort by need score (descending)
        ward_needs.sort(key=lambda x: x.need_score, reverse=True)
        
        # Allocate each resource type
        allocations = {}
        total_allocated = {}
        
        resource_configs = {
            "pumps": {"category": "flood", "min": 0},
            "buses": {"category": "flood", "min": 0},
            "relief_camps": {"category": "flood", "min": 0},
            "cooling_centers": {"category": "heat", "min": 0},
            "medical_units": {"category": "medical", "min": 0},
        }
        
        for resource_type, total in resources_available.items():
            if total <= 0:
                continue
            
            config = resource_configs.get(resource_type, {})
            constraint = ResourceConstraint(
                resource_type=resource_type,
                total_available=total,
                min_per_ward=config.get("min", 0)
            )
            
            resource_allocations = self.allocate_resource(ward_needs, constraint, use_delta)
            allocations[resource_type] = resource_allocations
            
            total_allocated[resource_type] = sum(
                a["allocated"] for a in resource_allocations.values()
            )
        
        # Generate explanations
        explanations = self._generate_explanations(ward_needs, allocations)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "scenario": scenario,
            "total_resources": resources_available,
            "total_allocated": total_allocated,
            "ward_allocations": self._format_ward_allocations(ward_needs, allocations),
            "explanations": explanations,
            "summary": {
                "total_wards": len(ward_needs),
                "critical_wards": sum(1 for wn in ward_needs if wn.flood_risk > self.critical_threshold or wn.heat_risk > self.critical_threshold),
                "highest_need_ward": ward_needs[0].ward_id if ward_needs else None,
            }
        }
    
    def _format_ward_allocations(
        self, 
        ward_needs: List[WardNeed], 
        allocations: Dict[str, Dict]
    ) -> List[Dict]:
        """Format allocations by ward"""
        result = []
        
        for wn in ward_needs:
            ward_alloc = {
                "ward_id": wn.ward_id,
                "ward_name": wn.ward_name,
                "population": wn.population,
                "risk": {
                    "flood": wn.flood_risk,
                    "heat": wn.heat_risk,
                    "delta": wn.risk_delta
                },
                "need_score": round(wn.need_score, 2),
                "resources": {}
            }
            
            for resource_type, resource_allocs in allocations.items():
                if wn.ward_id in resource_allocs:
                    ward_alloc["resources"][resource_type] = resource_allocs[wn.ward_id]
            
            result.append(ward_alloc)
        
        return result
    
    def _generate_explanations(
        self, 
        ward_needs: List[WardNeed], 
        allocations: Dict[str, Dict]
    ) -> Dict[str, str]:
        """Generate human-readable explanations for allocations"""
        explanations = {}
        
        # Top allocated ward explanation
        if ward_needs:
            top_ward = ward_needs[0]
            explanations["top_ward"] = (
                f"{top_ward.ward_name} receives highest allocation due to "
                f"risk score of {max(top_ward.flood_risk, top_ward.heat_risk):.0f}% "
                f"and population of {top_ward.population:,}."
            )
        
        # Critical wards explanation
        critical_wards = [
            wn for wn in ward_needs 
            if wn.flood_risk > self.critical_threshold or wn.heat_risk > self.critical_threshold
        ]
        
        if critical_wards:
            explanations["critical_wards"] = (
                f"{len(critical_wards)} wards classified as critical risk (>80%). "
                f"Minimum allocation of {self.min_allocation_critical} unit(s) guaranteed."
            )
        
        # Resource-specific explanations
        for resource_type, resource_allocs in allocations.items():
            top_ward_id = max(resource_allocs.items(), key=lambda x: x[1]["allocated"])[0]
            top_ward_data = next((wn for wn in ward_needs if wn.ward_id == top_ward_id), None)
            
            if top_ward_data:
                explanations[f"{resource_type}_top"] = (
                    f"Most {resource_type} allocated to {top_ward_data.ward_name} "
                    f"(need score: {top_ward_data.need_score:.1f})"
                )
        
        return explanations


# Singleton instance
allocator = ResourceAllocator()
