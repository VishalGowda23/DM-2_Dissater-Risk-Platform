"""
Alert Service
Generates templated, bilingual (English + Marathi) disaster alerts
for citizens and authorities based on risk levels.
"""
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
from types import SimpleNamespace
import logging

logger = logging.getLogger(__name__)


@dataclass
class Alert:
    """Generated alert"""
    alert_id: str
    ward_id: str
    ward_name: str
    alert_type: str          # citizen, authority
    priority: str            # advisory, watch, warning, emergency
    hazard: str              # flood, heat, compound
    risk_score: float
    title_en: str
    message_en: str
    title_mr: str            # Marathi
    message_mr: str
    actions: List[str]
    shelter_info: Optional[Dict]
    timestamp: str
    expires_at: str
    channel: str             # sms, whatsapp, push
    evacuation_route: Optional[Dict] = field(default=None)


# Shelter data for Pune wards
SHELTERS = {
    "W001": {"name": "Aundh Community Hall", "capacity": 500, "lat": 18.5583, "lon": 73.8073, "distance_km": 0.8},
    "W002": {"name": "Kothrud Vidya Vikas School", "capacity": 800, "lat": 18.5074, "lon": 73.8077, "distance_km": 1.1},
    "W003": {"name": "Warje Sports Complex", "capacity": 600, "lat": 18.4892, "lon": 73.7986, "distance_km": 0.9},
    "W004": {"name": "Shivaji Mandap (Kasba Peth)", "capacity": 400, "lat": 18.5136, "lon": 73.8567, "distance_km": 0.6},
    "W005": {"name": "Sarasbaug Shelter", "capacity": 700, "lat": 18.4983, "lon": 73.8547, "distance_km": 0.7},
    "W006": {"name": "Sinhagad Road Community Center", "capacity": 500, "lat": 18.4789, "lon": 73.8301, "distance_km": 1.2},
    "W007": {"name": "Sahakarnagar School", "capacity": 600, "lat": 18.4804, "lon": 73.8568, "distance_km": 0.5},
    "W008": {"name": "Bibwewadi Public Hall", "capacity": 450, "lat": 18.4745, "lon": 73.8615, "distance_km": 0.8},
    "W009": {"name": "Katraj Relief Camp", "capacity": 800, "lat": 18.4580, "lon": 73.8615, "distance_km": 1.0},
    "W010": {"name": "Deccan Gymkhana Hall", "capacity": 350, "lat": 18.5164, "lon": 73.8413, "distance_km": 0.4},
    "W011": {"name": "Nagar Road Community Center", "capacity": 600, "lat": 18.5564, "lon": 73.9133, "distance_km": 1.3},
    "W012": {"name": "Karve Nagar Relief Center", "capacity": 500, "lat": 18.4956, "lon": 73.8178, "distance_km": 0.7},
    "W013": {"name": "Hadapsar IT Park Shelter", "capacity": 900, "lat": 18.5030, "lon": 73.9350, "distance_km": 0.9},
    "W014": {"name": "Mundhwa Community Hall", "capacity": 400, "lat": 18.5291, "lon": 73.9213, "distance_km": 0.6},
    "W015": {"name": "Dhankawadi Public School", "capacity": 550, "lat": 18.4587, "lon": 73.8421, "distance_km": 1.1},
    "W016": {"name": "Kharadi IT Hub Shelter", "capacity": 700, "lat": 18.5481, "lon": 73.9422, "distance_km": 1.0},
    "W017": {"name": "Viman Nagar Community Center", "capacity": 600, "lat": 18.5667, "lon": 73.9146, "distance_km": 0.8},
    "W018": {"name": "Yerwada Relief Camp", "capacity": 500, "lat": 18.5515, "lon": 73.8874, "distance_km": 0.7},
    "W019": {"name": "Kondhwa Community Hall", "capacity": 450, "lat": 18.4635, "lon": 73.8859, "distance_km": 0.9},
    "W020": {"name": "Wagholi Emergency Center", "capacity": 800, "lat": 18.5804, "lon": 73.9819, "distance_km": 1.5},
}


class AlertService:
    """
    Generates context-aware disaster alerts for citizens and authorities.
    Includes bilingual support (English + Marathi) and channel-specific formatting.
    """

    def _compute_evacuation_route(self, ward_id: str, ward_name: str,
                                   centroid_lat: Optional[float], centroid_lon: Optional[float],
                                   risk_score: float) -> Optional[Dict]:
        """Compute evacuation route for a ward using EvacuationRouter."""
        try:
            from app.services.evacuation_router import evacuation_router as ev_router
            ward_obj = SimpleNamespace(
                ward_id=ward_id,
                name=ward_name,
                centroid_lat=centroid_lat or 18.5204,
                centroid_lon=centroid_lon or 73.8567,
            )
            risk_data = {"final_combined_risk": risk_score}
            route = ev_router.compute_evacuation_route(ward_obj, risk_data)
            # Return a compact summary
            best = route.get("recommended_shelter")
            if not best:
                return None
            return {
                "recommended_shelter": {
                    "name": best["shelter"]["name"],
                    "type": best["shelter"]["type"],
                    "capacity": best["shelter"]["capacity"],
                    "contact": best["shelter"]["contact"],
                    "facilities": best["shelter"]["facilities"],
                    "lat": best["shelter"]["lat"],
                    "lon": best["shelter"]["lon"],
                    "distance_km": best["distance_km"],
                    "travel_time_min": int(best["travel_time_min"]),
                },
                "route_coords": best["route_coords"],
                "route_safety": best["route_safety"],
                "evacuation_urgency": route["evacuation_urgency"],
                "alternatives": [
                    {
                        "name": a["shelter"]["name"],
                        "distance_km": a["distance_km"],
                        "travel_time_min": int(a["travel_time_min"]),
                        "route_coords": a["route_coords"],
                    }
                    for a in route.get("alternatives", [])[:2]
                ],
            }
        except Exception as e:
            logger.warning(f"Could not compute evacuation route for {ward_id}: {e}")
            return None

    alert_counter = 0

    def generate_alerts(
        self, risk_data: List[Dict], forecast_data: Dict = None,
        river_data: Dict = None
    ) -> Dict:
        """
        Generate alerts based on current risk, forecast, and river data.
        Returns alerts grouped by priority.
        """
        alerts = []
        
        for ward_risk in risk_data:
            ward_id = ward_risk.get("ward_id", "")
            ward_name = ward_risk.get("ward_name", "")
            risk_score = ward_risk.get("final_combined_risk", 0) or ward_risk.get("top_risk_score", 0) or 0
            top_hazard = ward_risk.get("top_hazard", "flood")
            # Default "none" hazard to "flood" for demo/alerting purposes
            if not top_hazard or top_hazard == "none":
                top_hazard = "flood"
            
            # Determine priority
            priority = self._get_priority(risk_score)
            if priority == "normal":
                continue  # No alert needed
            
            # Get forecast info for this ward
            forecast_info = self._get_forecast_info(ward_id, forecast_data)
            
            # Get shelter info
            shelter = SHELTERS.get(ward_id)

            # Compute evacuation route for watch+ priority alerts
            evac_route = None
            if priority in ["watch", "warning", "emergency"]:
                evac_route = self._compute_evacuation_route(
                    ward_id, ward_name,
                    ward_risk.get("centroid_lat"),
                    ward_risk.get("centroid_lon"),
                    risk_score,
                )

            # Generate citizen alert
            citizen_alert = self._generate_citizen_alert(
                ward_id, ward_name, risk_score, top_hazard, priority,
                shelter, forecast_info, evac_route
            )
            alerts.append(citizen_alert)

            # Generate authority alert for warning+ priorities
            if priority in ["warning", "emergency"]:
                auth_alert = self._generate_authority_alert(
                    ward_id, ward_name, risk_score, top_hazard, priority,
                    shelter, forecast_info, ward_risk, evac_route
                )
                alerts.append(auth_alert)
        
        # Always inject a demo alert so alerts tab is never empty
        if not alerts:
            alerts = self._build_demo_alerts()

        # Sort by priority severity
        priority_order = {"emergency": 0, "warning": 1, "watch": 2, "advisory": 3}
        alerts.sort(key=lambda a: priority_order.get(a.priority, 4))
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_alerts": len(alerts),
            "by_priority": {
                "emergency": len([a for a in alerts if a.priority == "emergency"]),
                "warning": len([a for a in alerts if a.priority == "warning"]),
                "watch": len([a for a in alerts if a.priority == "watch"]),
                "advisory": len([a for a in alerts if a.priority == "advisory"]),
            },
            "alerts": [asdict(a) for a in alerts],
        }

    def _generate_citizen_alert(
        self, ward_id: str, ward_name: str, risk_score: float,
        hazard: str, priority: str, shelter: Optional[Dict],
        forecast_info: Optional[Dict], evac_route: Optional[Dict] = None
    ) -> Alert:
        """Generate citizen-facing alert with shelter, evacuation route and action guidance"""
        self.alert_counter += 1
        
        # Build messages based on hazard + priority
        if hazard == "flood":
            title_en, message_en, title_mr, message_mr = self._flood_citizen_message(
                ward_name, risk_score, priority, shelter, forecast_info, evac_route
            )
        else:
            title_en, message_en, title_mr, message_mr = self._heat_citizen_message(
                ward_name, risk_score, priority, shelter, forecast_info
            )

        actions = self._get_citizen_actions(hazard, priority)
        # Prepend route action if available
        if evac_route and hazard == "flood":
            best = evac_route.get("recommended_shelter", {})
            if best:
                actions.insert(0, f"Evacuate to {best['name']} ({best['distance_km']}km, ~{best['travel_time_min']} min walk)")

        return Alert(
            alert_id=f"ALT-{self.alert_counter:04d}",
            ward_id=ward_id,
            ward_name=ward_name,
            alert_type="citizen",
            priority=priority,
            hazard=hazard,
            risk_score=round(risk_score, 1),
            title_en=title_en,
            message_en=message_en,
            title_mr=title_mr,
            message_mr=message_mr,
            actions=actions,
            shelter_info=shelter,
            timestamp=datetime.now().isoformat(),
            expires_at="",
            channel="sms" if priority == "emergency" else "whatsapp",
            evacuation_route=evac_route,
        )

    def _generate_authority_alert(
        self, ward_id: str, ward_name: str, risk_score: float,
        hazard: str, priority: str, shelter: Optional[Dict],
        forecast_info: Optional[Dict], ward_risk: Dict,
        evac_route: Optional[Dict] = None
    ) -> Alert:
        """Generate authority/PMC-facing alert with deployment recommendations"""
        self.alert_counter += 1
        
        pop = ward_risk.get("population", 100000)
        elderly_pct = ward_risk.get("elderly_ratio", 8)
        elderly_count = int(pop * elderly_pct / 100) if elderly_pct else int(pop * 0.08)
        
        if hazard == "flood":
            title_en = f"🚨 DEPLOY: Flood Response — {ward_name} ({ward_id})"
            route_line = ""
            if evac_route:
                best = evac_route.get("recommended_shelter", {})
                if best:
                    safety = evac_route.get("route_safety", {}).get("status", "safe")
                    avoid = evac_route.get("route_safety", {}).get("avoid_roads", [])
                    avoid_str = f" (avoid: {', '.join(avoid)}" + ")" if avoid else ""
                    alts = evac_route.get("alternatives", [])
                    alt_str = ""
                    if alts:
                        alt_str = f"\n• Alt shelter: {alts[0]['name']} ({alts[0]['distance_km']}km)"
                    route_line = (
                        f"\n• Evacuation route → {best['name']} ({best['distance_km']}km, ~{best['travel_time_min']} min) "
                        f"[{safety}]{avoid_str}"
                        f"\n• Shelter capacity: {best['capacity']}, contact: {best['contact']}"
                        f"\n• Facilities: {', '.join(best['facilities'])}"
                        f"{alt_str}"
                    )
            message_en = (
                f"FLOOD RISK {risk_score:.0f}% in {ward_name}.\n"
                f"ACTION REQUIRED:\n"
                f"• Deploy 5 water pumps to {ward_name}\n"
                f"• Pre-position 2 NDRF boats at nearest access point\n"
                f"• Notify {elderly_count:,} elderly residents via door-to-door\n"
                f"• Alert {shelter['name'] if shelter else 'nearest shelter'} "
                f"(capacity: {shelter['capacity'] if shelter else 'N/A'})"
                f"{route_line}"
            )
            title_mr = f"🚨 तैनाती: पूर प्रतिसाद — {ward_name}"
            mr_route = ""
            if evac_route:
                best = evac_route.get("recommended_shelter", {})
                if best:
                    mr_route = f"\nबाहेर पडण्याचा मार्ग: {best['name']} ({best['distance_km']}किमी)"
            message_mr = (
                f"पूर धोका {risk_score:.0f}% — {ward_name}\n"
                f"कृती आवश्यक: पंप तैनात करा, बचाव नौका तयार ठेवा"
                f"{mr_route}"
            )
        else:
            title_en = f"🌡️ DEPLOY: Heat Response — {ward_name} ({ward_id})"
            message_en = (
                f"HEAT RISK {risk_score:.0f}% in {ward_name}.\n"
                f"ACTION REQUIRED:\n"
                f"• Open cooling center at {shelter['name'] if shelter else 'community hall'}\n"
                f"• Deploy 2 mobile medical units\n"
                f"• Distribute ORS packets to vulnerable areas\n"
                f"• Alert hospitals: expected {int(pop * 0.002)} heat-related cases\n"
                f"• Water tanker deployment to {ward_name}"
            )
            title_mr = f"🌡️ तैनाती: उष्णता प्रतिसाद — {ward_name}"
            message_mr = (
                f"उष्णता धोका {risk_score:.0f}% — {ward_name}\n"
                f"कृती: शीतलन केंद्र उघडा, वैद्यकीय पथक पाठवा"
            )
        
        return Alert(
            alert_id=f"ALT-{self.alert_counter:04d}",
            ward_id=ward_id,
            ward_name=ward_name,
            alert_type="authority",
            priority=priority,
            hazard=hazard,
            risk_score=round(risk_score, 1),
            title_en=title_en,
            message_en=message_en,
            title_mr=title_mr,
            message_mr=message_mr,
            actions=self._get_authority_actions(hazard, priority),
            shelter_info=shelter,
            timestamp=datetime.now().isoformat(),
            expires_at="",
            channel="push",
            evacuation_route=evac_route,
        )

    def _flood_citizen_message(self, ward_name, risk, priority, shelter, forecast, evac_route=None):
        peak_info = ""
        if forecast:
            peak_info = f" Risk peaks at {forecast.get('peak_risk', risk):.0f}% in {forecast.get('peak_hours', '?')} hours."
        
        shelter_info = ""
        if shelter:
            shelter_info = f" Nearest shelter: {shelter['name']} ({shelter['distance_km']}km)."

        route_info = ""
        route_info_mr = ""
        if evac_route:
            best = evac_route.get("recommended_shelter", {})
            if best:
                safety = evac_route.get("route_safety", {}).get("status", "safe")
                avoid = evac_route.get("route_safety", {}).get("avoid_roads", [])
                avoid_str = f" Avoid: {', '.join(avoid)}." if avoid else ""
                route_info = (
                    f" EVACUATION ROUTE: Head to {best['name']} ({best['distance_km']}km, ~{best['travel_time_min']} min walk)."
                    f" Route is [{safety}].{avoid_str}"
                )
                route_info_mr = f" बाहेर पडण्याचा मार्ग: {best['name']} ({best['distance_km']}किमी, ~{best['travel_time_min']} मिनिटे)."

        if priority == "emergency":
            title_en = f"🔴 EMERGENCY FLOOD ALERT — {ward_name}"
            message_en = (f"⚠️ FLOOD WARNING: Your area ({ward_name}) faces {risk:.0f}% flood risk.{peak_info}"
                         f" Move to higher ground IMMEDIATELY.{shelter_info}{route_info}"
                         f" Avoid waterlogged roads. Call 112 for emergency.")
            title_mr = f"🔴 आपत्कालीन पूर सूचना — {ward_name}"
            message_mr = (f"⚠️ पूर चेतावणी: तुमचे क्षेत्र ({ward_name}) ला {risk:.0f}% पूर धोका."
                         f"{route_info_mr} तात्काळ उंच भागात जा. आपत्कालीन मदतीसाठी 112 वर कॉल करा.")
        elif priority == "warning":
            title_en = f"🟠 FLOOD WARNING — {ward_name}"
            message_en = (f"Flood risk rising to {risk:.0f}% in {ward_name}.{peak_info}"
                         f" Prepare to evacuate if notified.{shelter_info}{route_info}"
                         f" Keep emergency kit ready.")
            title_mr = f"🟠 पूर चेतावणी — {ward_name}"
            message_mr = f"पूर धोका {risk:.0f}% — {ward_name}.{route_info_mr} आपत्कालीन किट तयार ठेवा."
        else:
            title_en = f"🟡 FLOOD WATCH — {ward_name}"
            message_en = (f"Elevated flood risk ({risk:.0f}%) in {ward_name}.{peak_info}"
                         f" Stay alert for updates.{shelter_info}{route_info}")
            title_mr = f"🟡 पूर निरीक्षण — {ward_name}"
            message_mr = f"वाढता पूर धोका ({risk:.0f}%) — {ward_name}.{route_info_mr} सतर्क रहा."

        return title_en, message_en, title_mr, message_mr

    def _heat_citizen_message(self, ward_name, risk, priority, shelter, forecast):
        shelter_info = ""
        if shelter:
            shelter_info = f" Cooling center: {shelter['name']} ({shelter['distance_km']}km)."
        
        if priority == "emergency":
            title_en = f"🔴 EXTREME HEAT EMERGENCY — {ward_name}"
            message_en = (f"🌡️ HEAT EMERGENCY: {ward_name} heat risk at {risk:.0f}%."
                         f" Stay indoors. Drink water every 30 min.{shelter_info}"
                         f" Check on elderly neighbors. Call 108 for medical help.")
            title_mr = f"🔴 अत्यंत उष्णता आपत्कालीन — {ward_name}"
            message_mr = f"🌡️ उष्णता आपत्कालीन: {ward_name} मध्ये {risk:.0f}% धोका. घरी रहा, पाणी प्या."
        elif priority == "warning":
            title_en = f"🟠 HEAT WARNING — {ward_name}"
            message_en = (f"Heat risk at {risk:.0f}% in {ward_name}. Avoid outdoor activity 11AM-4PM."
                         f" Hydrate frequently.{shelter_info}")
            title_mr = f"🟠 उष्णता चेतावणी — {ward_name}"
            message_mr = f"उष्णता धोका {risk:.0f}% — {ward_name}. दुपारी बाहेर जाणे टाळा."
        else:
            title_en = f"🟡 HEAT ADVISORY — {ward_name}"
            message_en = f"Heat index elevated ({risk:.0f}%) in {ward_name}. Stay hydrated.{shelter_info}"
            title_mr = f"🟡 उष्णता सल्ला — {ward_name}"
            message_mr = f"वाढता उष्णता निर्देशांक ({risk:.0f}%) — {ward_name}."

        return title_en, message_en, title_mr, message_mr

    def _get_citizen_actions(self, hazard: str, priority: str) -> List[str]:
        if hazard == "flood":
            actions = ["Move valuables to upper floors", "Keep emergency kit ready"]
            if priority in ["warning", "emergency"]:
                actions += [
                    "Move to nearest shelter if water enters ground floor",
                    "Do not drive through waterlogged roads",
                    "Call 112 / NDRF for rescue",
                ]
        else:
            actions = ["Stay hydrated — drink water every 30 minutes", "Avoid outdoor work 11AM-4PM"]
            if priority in ["warning", "emergency"]:
                actions += [
                    "Visit nearest cooling center",
                    "Check on elderly/vulnerable neighbors",
                    "Call 108 for heat-related medical emergency",
                ]
        return actions

    def _get_authority_actions(self, hazard: str, priority: str) -> List[str]:
        if hazard == "flood":
            return [
                "Deploy water pumps to affected areas",
                "Position NDRF rescue teams",
                "Open evacuation routes",
                "Activate relief camps",
                "Alert hospitals for trauma preparedness",
            ]
        else:
            return [
                "Open cooling centers in high-risk wards",
                "Deploy mobile medical units",
                "Ensure water tanker supply",
                "Issue public heat advisory",
                "Alert hospitals for heat stroke cases",
            ]

    # ─── Demo Alert (always present) ──────────────────────────────────────────
    def _build_demo_alerts(self) -> List:
        """
        Return a small set of realistic demo alerts so the Alerts tab is
        never empty — even when current weather is calm.
        """
        now = datetime.now().isoformat()
        demo_ward = "W004"
        demo_ward_name = "Kasba Peth"
        demo_risk = 78.0
        demo_priority = "warning"
        demo_hazard = "flood"
        shelter = SHELTERS.get(demo_ward, {})

        # Compute a real evacuation route for the demo ward
        evac_route = self._compute_evacuation_route(
            demo_ward, demo_ward_name, 18.5155, 73.8563, demo_risk
        )

        # --- Citizen alert ---
        self.alert_counter += 1
        citizen = Alert(
            alert_id=f"ALT-{self.alert_counter:04d}",
            ward_id=demo_ward,
            ward_name=demo_ward_name,
            alert_type="citizen",
            priority=demo_priority,
            hazard=demo_hazard,
            risk_score=demo_risk,
            title_en=f"🟠 FLOOD WARNING — {demo_ward_name}",
            message_en=(
                f"Flood risk rising to {demo_risk:.0f}% in {demo_ward_name}. "
                "Prepare to evacuate if notified. "
                f"Nearest shelter: {shelter.get('name', 'N/A')} ({shelter.get('distance_km', '?')}km)."
                + (f" EVACUATION ROUTE: Head to {evac_route['recommended_shelter']['name']} "
                   f"({evac_route['recommended_shelter']['distance_km']}km, "
                   f"~{evac_route['recommended_shelter'].get('walk_time_min', evac_route['recommended_shelter'].get('travel_time_min','?'))} min walk). "
                   f"Route is [{evac_route.get('route_safety', {}).get('status', 'safe')}]."
                   if evac_route else "")
            ),
            title_mr=f"🟠 पूर चेतावनी — {demo_ward_name}",
            message_mr=(
                f"वाढता पूर धोका ({demo_risk:.0f}%) — {demo_ward_name}. "
                "सूचना मिळाल्यास स्थलांतरासाठी तयार रहा. "
                + (f"बाहेर पडण्याचा मार्ग: {evac_route['recommended_shelter']['name']} "
                   f"({evac_route['recommended_shelter']['distance_km']}किमी, "
                   f"~{evac_route['recommended_shelter'].get('walk_time_min', evac_route['recommended_shelter'].get('travel_time_min','?'))} मिनिटे). "
                   f"सतर्क रहा."
                   if evac_route else "")
            ),
            actions=[
                f"Evacuate to {evac_route['recommended_shelter']['name']} ({evac_route['recommended_shelter']['distance_km']}km)" if evac_route else "Move to higher ground",
                "Move valuables to upper floors",
                "Keep emergency kit ready",
                "Follow PMC updates on radio / WhatsApp",
            ],
            shelter_info=shelter or None,
            timestamp=now,
            expires_at="",
            channel="whatsapp",
            evacuation_route=evac_route,
        )

        # --- Authority alert ---
        self.alert_counter += 1
        authority = Alert(
            alert_id=f"ALT-{self.alert_counter:04d}",
            ward_id=demo_ward,
            ward_name=demo_ward_name,
            alert_type="authority",
            priority=demo_priority,
            hazard=demo_hazard,
            risk_score=demo_risk,
            title_en=f"⚠️ AUTHORITY ALERT — {demo_ward_name} (Flood {demo_risk:.0f}%)",
            message_en=(
                f"Ward {demo_ward} ({demo_ward_name}) flood risk at {demo_risk:.0f}%. "
                "Population: ~145,000. Elderly ratio: 12%. "
                "Recommended: pre-position 3 pumps, 2 rescue boats. "
                f"Primary shelter: {shelter.get('name', 'N/A')} (capacity {shelter.get('capacity', '?')})."
                + (f"\nEvacuation route: {evac_route['recommended_shelter']['name']} "
                   f"({evac_route['recommended_shelter']['distance_km']}km). "
                   f"Contact: {evac_route['recommended_shelter'].get('contact', 'N/A')}."
                   if evac_route else "")
            ),
            title_mr=f"⚠️ अधिकारी सूचना — {demo_ward_name} (पूर {demo_risk:.0f}%)",
            message_mr=(
                f"प्रभाग {demo_ward} ({demo_ward_name}) पूर धोका {demo_risk:.0f}%. "
                "लोकसंख्या: ~१,४५,०००. वृद्ध प्रमाण: १२%. "
                "शिफारस: ३ पंप, २ बचाव नौका तैनात करा."
            ),
            actions=[
                "Deploy 3 water pumps to Kasba Peth",
                "Pre-position 2 rescue boats at Mutha river bank",
                f"Open {shelter.get('name', 'shelter')} for evacuees",
                "Alert NDRF Pune unit on standby",
                "Close low-lying road segments near Lakdi Pul",
            ],
            shelter_info=shelter or None,
            timestamp=now,
            expires_at="",
            channel="sms",
            evacuation_route=evac_route,
        )

        return [citizen, authority]

    def _get_priority(self, risk_score: float) -> str:
        if risk_score >= 80:
            return "emergency"
        if risk_score >= 65:
            return "warning"
        if risk_score >= 50:
            return "watch"
        if risk_score >= 35:
            return "advisory"
        return "normal"

    def _get_forecast_info(self, ward_id: str, forecast_data: Dict = None) -> Optional[Dict]:
        if not forecast_data:
            return None
        forecasts = forecast_data.get("forecasts", [])
        for f in forecasts:
            if f.get("ward_id") == ward_id:
                peak = f.get("peak", {})
                return {
                    "peak_risk": peak.get("risk", 0),
                    "peak_hours": peak.get("hour", 0),
                    "trend": f.get("trend", "unknown"),
                }
        return None


# Global instance
alert_service = AlertService()
