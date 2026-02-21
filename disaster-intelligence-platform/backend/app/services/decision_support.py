"""
Decision Support System
Aggregates all signals (risk, forecast, rivers, alerts) into
prioritized, actionable recommendations for disaster authorities.
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class ActionItem:
    """A prioritized action recommendation"""
    action_id: str
    priority: str          # immediate, next_6h, next_24h, advisory
    category: str          # deploy, evacuate, alert, monitor, prepare
    ward_id: str
    ward_name: str
    title: str
    description: str
    justification: str     # Why this action is recommended
    resources_needed: List[Dict]
    estimated_impact: str  # What happens if this is/isn't done
    status: str            # pending, acknowledged, deployed, resolved
    assigned_to: str
    deadline: str
    created_at: str


class DecisionSupportSystem:
    """
    Command-center decision support.
    Aggregates risk scores, forecasts, river levels, and alerts
    into a prioritized action plan for PMC disaster response.
    """

    action_counter = 0

    def generate_action_plan(
        self,
        risk_data: List[Dict],
        forecast_data: Dict = None,
        river_data: Dict = None,
        optimization_data: Dict = None,
    ) -> Dict:
        """
        Generate complete decision support action plan.
        
        Inputs:
        - risk_data: Current ward risk scores
        - forecast_data: 48h forecast from ForecastEngine
        - river_data: River levels from RiverMonitor
        - optimization_data: Resource allocation from Optimizer
        """
        actions = []
        
        # 1. Critical risk actions (based on current risk)
        actions.extend(self._generate_risk_actions(risk_data))
        
        # 2. Forecast-based precautionary actions
        if forecast_data:
            actions.extend(self._generate_forecast_actions(forecast_data))
        
        # 3. River level actions
        if river_data:
            actions.extend(self._generate_river_actions(river_data))
        
        # 4. Resource deployment actions
        if optimization_data:
            actions.extend(self._generate_deployment_actions(optimization_data))
        
        # Sort by priority
        priority_order = {"immediate": 0, "next_6h": 1, "next_24h": 2, "advisory": 3}
        actions.sort(key=lambda a: priority_order.get(a.priority, 4))
        
        # Generate KPIs
        kpis = self._compute_kpis(actions, risk_data)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "situation_level": self._get_situation_level(actions),
            "kpis": kpis,
            "total_actions": len(actions),
            "by_priority": {
                "immediate": len([a for a in actions if a.priority == "immediate"]),
                "next_6h": len([a for a in actions if a.priority == "next_6h"]),
                "next_24h": len([a for a in actions if a.priority == "next_24h"]),
                "advisory": len([a for a in actions if a.priority == "advisory"]),
            },
            "actions": [asdict(a) for a in actions],
        }

    def _generate_risk_actions(self, risk_data: List[Dict]) -> List[ActionItem]:
        """Generate actions based on current risk scores"""
        actions = []
        
        for ward_risk in risk_data:
            risk = ward_risk.get("final_combined_risk", 0) or ward_risk.get("top_risk_score", 0) or 0
            ward_id = ward_risk.get("ward_id", "")
            ward_name = ward_risk.get("ward_name", "")
            hazard = ward_risk.get("top_hazard", "flood")
            pop = ward_risk.get("population", 100000)
            
            if risk >= 80:
                # IMMEDIATE action for critical wards
                self.action_counter += 1
                if hazard == "flood":
                    actions.append(ActionItem(
                        action_id=f"ACT-{self.action_counter:04d}",
                        priority="immediate",
                        category="deploy",
                        ward_id=ward_id,
                        ward_name=ward_name,
                        title=f"Deploy flood response to {ward_name}",
                        description=(
                            f"Flood risk at {risk:.0f}%. Deploy 5 water pumps, "
                            f"2 NDRF rescue boats, and open evacuation route. "
                            f"Notify {int(pop * 0.08):,} elderly residents."
                        ),
                        justification=(
                            f"Risk score exceeds critical threshold (80%). "
                            f"Population of {pop:,} at risk. Historical flood frequency "
                            f"indicates high vulnerability."
                        ),
                        resources_needed=[
                            {"type": "water_pumps", "count": 5},
                            {"type": "ndrf_boats", "count": 2},
                            {"type": "rescue_teams", "count": 3},
                        ],
                        estimated_impact=f"Without action: ~{int(pop * 0.02):,} people stranded, "
                                        f"₹{int(risk * pop / 10000):,}L property damage estimated",
                        status="pending",
                        assigned_to="NDRF + PMC Disaster Cell",
                        deadline=(datetime.now() + timedelta(hours=2)).isoformat(),
                        created_at=datetime.now().isoformat(),
                    ))
                else:
                    self.action_counter += 1
                    actions.append(ActionItem(
                        action_id=f"ACT-{self.action_counter:04d}",
                        priority="immediate",
                        category="deploy",
                        ward_id=ward_id,
                        ward_name=ward_name,
                        title=f"Open cooling centers in {ward_name}",
                        description=(
                            f"Heat risk at {risk:.0f}%. Open all cooling centers, "
                            f"deploy 2 mobile medical units, distribute ORS packets."
                        ),
                        justification=(
                            f"Heat risk critical. Elderly population ({int(pop * 0.08):,}) "
                            f"particularly vulnerable. Hospital surge expected."
                        ),
                        resources_needed=[
                            {"type": "cooling_centers", "count": 2},
                            {"type": "medical_units", "count": 2},
                            {"type": "water_tankers", "count": 3},
                        ],
                        estimated_impact=f"Without action: ~{int(risk * 0.5):.0f} heat stroke cases, "
                                        f"{int(pop * 0.001):,} hospitalizations",
                        status="pending",
                        assigned_to="PMC Health Dept",
                        deadline=(datetime.now() + timedelta(hours=3)).isoformat(),
                        created_at=datetime.now().isoformat(),
                    ))
            
            elif risk >= 65:
                # NEXT 6H: prepare for high-risk wards
                self.action_counter += 1
                actions.append(ActionItem(
                    action_id=f"ACT-{self.action_counter:04d}",
                    priority="next_6h",
                    category="prepare",
                    ward_id=ward_id,
                    ward_name=ward_name,
                    title=f"Pre-position resources for {ward_name}",
                    description=(
                        f"Risk at {risk:.0f}% and may escalate. "
                        f"Pre-position 3 pumps and 1 rescue team at {ward_name} staging area. "
                        f"Verify shelter readiness."
                    ),
                    justification=f"Risk trending toward critical. Early positioning reduces response time by 45 minutes.",
                    resources_needed=[
                        {"type": "pumps", "count": 3},
                        {"type": "rescue_teams", "count": 1},
                    ],
                    estimated_impact="Pre-positioning reduces response time from 90 min to 45 min",
                    status="pending",
                    assigned_to="PMC Fire Brigade",
                    deadline=(datetime.now() + timedelta(hours=6)).isoformat(),
                    created_at=datetime.now().isoformat(),
                ))
            
            elif risk >= 50:
                # ADVISORY: monitor
                self.action_counter += 1
                actions.append(ActionItem(
                    action_id=f"ACT-{self.action_counter:04d}",
                    priority="advisory",
                    category="monitor",
                    ward_id=ward_id,
                    ward_name=ward_name,
                    title=f"Monitor {ward_name} — elevated risk",
                    description=f"Risk at {risk:.0f}%. Maintain monitoring, verify communication channels.",
                    justification="Moderate risk level warrants active monitoring.",
                    resources_needed=[],
                    estimated_impact="No immediate action needed, but situation may evolve.",
                    status="pending",
                    assigned_to="Ward Officer",
                    deadline=(datetime.now() + timedelta(hours=12)).isoformat(),
                    created_at=datetime.now().isoformat(),
                ))
        
        return actions

    def _generate_forecast_actions(self, forecast_data: Dict) -> List[ActionItem]:
        """Generate actions based on 48h forecast predictions"""
        actions = []
        forecasts = forecast_data.get("forecasts", [])
        
        for ward_fc in forecasts:
            peak = ward_fc.get("peak", {})
            peak_risk = peak.get("risk", 0)
            peak_hour = peak.get("hour", 0)
            trend = ward_fc.get("trend", "stable")
            time_to_critical = ward_fc.get("time_to_critical")
            ward_id = ward_fc.get("ward_id", "")
            ward_name = ward_fc.get("ward_name", "")
            
            if trend == "rising" and peak_risk >= 70 and peak_hour > 6:
                self.action_counter += 1
                actions.append(ActionItem(
                    action_id=f"ACT-{self.action_counter:04d}",
                    priority="next_6h",
                    category="prepare",
                    ward_id=ward_id,
                    ward_name=ward_name,
                    title=f"Forecast: {ward_name} risk peaks at {peak_risk:.0f}% in {peak_hour}h",
                    description=(
                        f"Risk trajectory shows {ward_name} reaching {peak_risk:.0f}% "
                        f"in {peak_hour} hours. Pre-position resources NOW for proactive response."
                    ),
                    justification=(
                        f"48-hour forecast model predicts rising risk with peak at T+{peak_hour}h. "
                        f"Time-to-critical: {time_to_critical}h. Proactive deployment saves lives."
                    ),
                    resources_needed=[
                        {"type": "pumps", "count": 3},
                        {"type": "evacuation_buses", "count": 2},
                    ],
                    estimated_impact=f"Acting {peak_hour}h before peak gives 3x more effective response",
                    status="pending",
                    assigned_to="PMC Disaster Cell",
                    deadline=(datetime.now() + timedelta(hours=max(1, peak_hour - 4))).isoformat(),
                    created_at=datetime.now().isoformat(),
                ))
        
        # Danger window action
        danger_window = forecast_data.get("danger_window")
        if danger_window:
            self.action_counter += 1
            actions.append(ActionItem(
                action_id=f"ACT-{self.action_counter:04d}",
                priority="next_6h",
                category="alert",
                ward_id="CITY",
                ward_name="Pune City",
                title=f"DANGER WINDOW: T+{danger_window['start_hour']}h to T+{danger_window['end_hour']}h",
                description=(
                    f"Multiple wards will exceed critical risk levels between "
                    f"T+{danger_window['start_hour']}h and T+{danger_window['end_hour']}h. "
                    f"Activate city-wide emergency response protocol."
                ),
                justification="Models predict synchronized risk escalation across multiple wards.",
                resources_needed=[],
                estimated_impact="City-wide coordination reduces mortality by 60%",
                status="pending",
                assigned_to="District Collector + PMC Commissioner",
                deadline=danger_window["start_time"],
                created_at=datetime.now().isoformat(),
            ))
        
        return actions

    def _generate_river_actions(self, river_data: Dict) -> List[ActionItem]:
        """Generate actions based on river level data"""
        actions = []
        stations = river_data.get("stations", {})
        
        for station_id, level_info in stations.items():
            stage = level_info.get("flood_stage", "normal")
            station = level_info.get("station", {})
            trend = level_info.get("trend", "stable")
            time_to_danger = level_info.get("time_to_danger_hours")
            
            if stage in ["danger", "extreme"]:
                self.action_counter += 1
                nearby = station.get("nearby_wards", [])
                actions.append(ActionItem(
                    action_id=f"ACT-{self.action_counter:04d}",
                    priority="immediate",
                    category="evacuate",
                    ward_id=nearby[0] if nearby else "RIVER",
                    ward_name=station.get("name", ""),
                    title=f"RIVER ALERT: {station.get('name', '')} at {stage.upper()} level",
                    description=(
                        f"River {station.get('river', '')} at {station.get('name', '')} "
                        f"has reached {stage} level ({level_info.get('level_pct_of_danger', 0):.0f}% of danger). "
                        f"Evacuate low-lying areas in wards: {', '.join(nearby)}."
                    ),
                    justification=f"CWC flood stage: {stage}. Trend: {trend}.",
                    resources_needed=[
                        {"type": "rescue_boats", "count": 3},
                        {"type": "evacuation_buses", "count": 5},
                    ],
                    estimated_impact=f"Affected wards: {', '.join(nearby)}. Immediate evacuation needed.",
                    status="pending",
                    assigned_to="NDRF + District Disaster Cell",
                    deadline=(datetime.now() + timedelta(hours=1)).isoformat(),
                    created_at=datetime.now().isoformat(),
                ))
            
            elif stage == "warning" and trend in ["rising", "rising_fast"]:
                self.action_counter += 1
                nearby = station.get("nearby_wards", [])
                actions.append(ActionItem(
                    action_id=f"ACT-{self.action_counter:04d}",
                    priority="next_6h",
                    category="prepare",
                    ward_id=nearby[0] if nearby else "RIVER",
                    ward_name=station.get("name", ""),
                    title=f"River rising at {station.get('name', '')} — prepare evacuation",
                    description=(
                        f"River level at warning stage and {trend}. "
                        f"Estimated {time_to_danger or '?'}h to danger level. "
                        f"Prepare evacuation for {', '.join(nearby)}."
                    ),
                    justification=f"Rising trend with {time_to_danger or '?'}h to danger.",
                    resources_needed=[
                        {"type": "standby_teams", "count": 2},
                    ],
                    estimated_impact="Early preparation reduces response time by 50%.",
                    status="pending",
                    assigned_to="PMC Fire Brigade",
                    deadline=(datetime.now() + timedelta(hours=3)).isoformat(),
                    created_at=datetime.now().isoformat(),
                ))
        
        return actions

    def _generate_deployment_actions(self, optimization_data: Dict) -> List[ActionItem]:
        """Generate actions based on resource optimization results"""
        actions = []
        
        ward_allocations = optimization_data.get("ward_allocations", [])
        for wa in ward_allocations[:5]:  # Top 5 wards only
            resources = wa.get("resources", {})
            total_units = sum(r.get("allocated", 0) for r in resources.values())
            
            if total_units > 0:
                self.action_counter += 1
                resource_list = []
                for rtype, rdata in resources.items():
                    if rdata.get("allocated", 0) > 0:
                        resource_list.append(
                            {"type": rtype, "count": rdata["allocated"]}
                        )
                
                actions.append(ActionItem(
                    action_id=f"ACT-{self.action_counter:04d}",
                    priority="next_24h",
                    category="deploy",
                    ward_id=wa.get("ward_id", ""),
                    ward_name=wa.get("ward_name", ""),
                    title=f"Deploy {total_units} units to {wa.get('ward_name', '')}",
                    description=(
                        f"Optimized allocation recommends {total_units} resource units "
                        f"for {wa.get('ward_name', '')} based on need score {wa.get('need_score', 0):.0f}."
                    ),
                    justification="Resource optimizer proportional allocation based on risk × population.",
                    resources_needed=resource_list,
                    estimated_impact=f"Covers population of {wa.get('population', 0):,}",
                    status="pending",
                    assigned_to="PMC Resource Cell",
                    deadline=(datetime.now() + timedelta(hours=24)).isoformat(),
                    created_at=datetime.now().isoformat(),
                ))
        
        return actions

    def _compute_kpis(self, actions: List[ActionItem], risk_data: List[Dict]) -> Dict:
        """Compute key performance indicators"""
        critical_wards = sum(
            1 for r in risk_data
            if (r.get("final_combined_risk", 0) or r.get("top_risk_score", 0) or 0) >= 80
        )
        total_pop_at_risk = sum(
            r.get("population", 0)
            for r in risk_data
            if (r.get("final_combined_risk", 0) or r.get("top_risk_score", 0) or 0) >= 60
        )
        
        return {
            "critical_actions_pending": len([a for a in actions if a.priority == "immediate" and a.status == "pending"]),
            "total_actions": len(actions),
            "critical_wards": critical_wards,
            "population_at_risk": total_pop_at_risk,
            "response_readiness": "HIGH" if critical_wards == 0 else ("LOW" if critical_wards > 3 else "MODERATE"),
            "deployed": len([a for a in actions if a.status == "deployed"]),
            "resolved": len([a for a in actions if a.status == "resolved"]),
        }

    def _get_situation_level(self, actions: List[ActionItem]) -> str:
        """Determine overall situation level"""
        immediate = len([a for a in actions if a.priority == "immediate"])
        if immediate >= 3:
            return "RED"
        if immediate >= 1:
            return "ORANGE"
        next_6h = len([a for a in actions if a.priority == "next_6h"])
        if next_6h >= 3:
            return "YELLOW"
        return "GREEN"


# Global instance
decision_support = DecisionSupportSystem()
