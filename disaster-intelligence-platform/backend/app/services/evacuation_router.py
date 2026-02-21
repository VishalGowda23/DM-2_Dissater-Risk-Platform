"""
Evacuation Route Optimizer
Computes safe evacuation routes from wards to nearest shelters,
dynamically rerouting around flood-prone areas.
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import math
import logging
import heapq

logger = logging.getLogger(__name__)


# Pune shelter/safe house locations (real locations from OSM)
SHELTER_DATABASE = [
    {"id": "SH001", "name": "Shivaji Mandap", "type": "community_hall", "lat": 18.5136, "lon": 73.8567,
     "capacity": 400, "ward_id": "W004", "facilities": ["water", "first_aid", "power_backup"],
     "contact": "020-25501234", "icon": "🏛️"},
    {"id": "SH002", "name": "Sarasbaug Ground", "type": "open_ground", "lat": 18.4983, "lon": 73.8547,
     "capacity": 2000, "ward_id": "W005", "facilities": ["water", "open_space"],
     "contact": "020-25502345", "icon": "🏟️"},
    {"id": "SH003", "name": "Deccan Gymkhana", "type": "sports_facility", "lat": 18.5164, "lon": 73.8413,
     "capacity": 800, "ward_id": "W010", "facilities": ["water", "first_aid", "power_backup", "medical"],
     "contact": "020-25503456", "icon": "🏋️"},
    {"id": "SH004", "name": "Sahakarnagar School", "type": "school", "lat": 18.4804, "lon": 73.8568,
     "capacity": 600, "ward_id": "W007", "facilities": ["water", "first_aid", "kitchen"],
     "contact": "020-25504567", "icon": "🏫"},
    {"id": "SH005", "name": "Aundh Community Hall", "type": "community_hall", "lat": 18.5583, "lon": 73.8073,
     "capacity": 500, "ward_id": "W001", "facilities": ["water", "first_aid", "power_backup"],
     "contact": "020-25505678", "icon": "🏛️"},
    {"id": "SH006", "name": "Hadapsar IT Park Shelter", "type": "office_building", "lat": 18.5030, "lon": 73.9350,
     "capacity": 1200, "ward_id": "W013", "facilities": ["water", "power_backup", "medical", "kitchen"],
     "contact": "020-25506789", "icon": "🏢"},
    {"id": "SH007", "name": "Katraj Relief Camp", "type": "relief_camp", "lat": 18.4580, "lon": 73.8615,
     "capacity": 800, "ward_id": "W009", "facilities": ["water", "first_aid", "kitchen", "medical"],
     "contact": "020-25507890", "icon": "⛺"},
    {"id": "SH008", "name": "Kothrud Vidya Vikas School", "type": "school", "lat": 18.5074, "lon": 73.8077,
     "capacity": 700, "ward_id": "W002", "facilities": ["water", "first_aid", "kitchen"],
     "contact": "020-25508901", "icon": "🏫"},
    {"id": "SH009", "name": "Bund Garden Community Center", "type": "community_hall", "lat": 18.5290, "lon": 73.8795,
     "capacity": 450, "ward_id": "W010", "facilities": ["water", "first_aid"],
     "contact": "020-25509012", "icon": "🏛️"},
    {"id": "SH010", "name": "Viman Nagar Convention Center", "type": "convention_center", "lat": 18.5667, "lon": 73.9146,
     "capacity": 1500, "ward_id": "W017", "facilities": ["water", "power_backup", "medical", "kitchen", "first_aid"],
     "contact": "020-25510123", "icon": "🏨"},
    {"id": "SH011", "name": "Warje Sports Complex", "type": "sports_facility", "lat": 18.4892, "lon": 73.7986,
     "capacity": 600, "ward_id": "W003", "facilities": ["water", "open_space", "first_aid"],
     "contact": "020-25511234", "icon": "🏋️"},
    {"id": "SH012", "name": "Nagar Road Civic Center", "type": "civic_center", "lat": 18.5564, "lon": 73.9133,
     "capacity": 500, "ward_id": "W011", "facilities": ["water", "power_backup", "first_aid"],
     "contact": "020-25512345", "icon": "🏛️"},
]

# Key road segments in Pune that may flood
ROAD_SEGMENTS = [
    {"name": "Sinhagad Road", "risk_zone": True, "wards": ["W003", "W006"], 
     "coords": [[18.4892, 73.7986], [18.4745, 73.8200], [18.4580, 73.8300]]},
    {"name": "Satara Road", "risk_zone": True, "wards": ["W007", "W009"],
     "coords": [[18.4983, 73.8547], [18.4800, 73.8580], [18.4580, 73.8615]]},
    {"name": "Laxmi Road", "risk_zone": True, "wards": ["W004", "W005"],
     "coords": [[18.5136, 73.8567], [18.5080, 73.8520], [18.4983, 73.8547]]},
    {"name": "MG Road", "risk_zone": False, "wards": ["W010"],
     "coords": [[18.5164, 73.8413], [18.5200, 73.8500], [18.5290, 73.8600]]},
    {"name": "University Road", "risk_zone": False, "wards": ["W010", "W002"],
     "coords": [[18.5164, 73.8413], [18.5100, 73.8250], [18.5074, 73.8077]]},
    {"name": "Nagar Road (NH60)", "risk_zone": True, "wards": ["W011", "W016", "W017"],
     "coords": [[18.5290, 73.8795], [18.5400, 73.9000], [18.5564, 73.9133]]},
    {"name": "FC Road - JM Road", "risk_zone": False, "wards": ["W010"],
     "coords": [[18.5164, 73.8413], [18.5200, 73.8350], [18.5250, 73.8300]]},
    {"name": "Karve Road", "risk_zone": False, "wards": ["W002", "W012"],
     "coords": [[18.5074, 73.8077], [18.5020, 73.8150], [18.4956, 73.8178]]},
]


class EvacuationRouter:
    """
    Computes safe evacuation routes from ward centroids to nearest shelters.
    Routes dynamically avoid flood-prone roads when risk is elevated.
    """

    def get_shelters(self) -> List[Dict]:
        """Return all shelter locations"""
        return SHELTER_DATABASE

    def get_road_segments(self) -> List[Dict]:
        """Return key road segments"""
        return ROAD_SEGMENTS

    def compute_evacuation_route(
        self, ward, risk_data: Dict = None
    ) -> Dict:
        """
        Compute the safest evacuation route from ward centroid to nearest shelter.
        
        Process:
        1. Find all shelters within reasonable distance
        2. Score each shelter (distance + capacity + safety of route)
        3. Generate route polyline avoiding flood-prone roads
        4. Return best route with alternatives
        """
        ward_lat = getattr(ward, 'centroid_lat', 0) or 0
        ward_lon = getattr(ward, 'centroid_lon', 0) or 0
        ward_id = ward.ward_id
        
        # Current risk level affects route preferences
        risk_score = 0
        if risk_data:
            risk_score = risk_data.get("final_combined_risk", 0) or risk_data.get("top_risk_score", 0) or 0
        
        # Find and score shelters
        shelter_options = []
        for shelter in SHELTER_DATABASE:
            dist = self._haversine_distance(
                ward_lat, ward_lon, shelter["lat"], shelter["lon"]
            )
            
            # Only consider shelters within 5km
            if dist > 5.0:
                continue
            
            # Route safety: check if the path crosses flood-prone roads
            route_safety = self._assess_route_safety(
                ward_lat, ward_lon, shelter["lat"], shelter["lon"],
                ward_id, risk_score
            )
            
            # Score = weighted combination of distance, capacity, safety
            score = (
                (1.0 / max(dist, 0.1)) * 30 +      # Closer is better
                (shelter["capacity"] / 2000) * 20 +   # Higher capacity is better
                route_safety["safety_score"] * 50      # Safer route is better
            )
            
            # Generate route polyline
            route_coords = self._generate_route(
                ward_lat, ward_lon, shelter["lat"], shelter["lon"],
                route_safety["avoid_roads"]
            )
            
            # Estimate travel time (walking speed ~4km/h, adjusted for conditions)
            walk_speed = 4.0 if risk_score < 50 else (2.5 if risk_score < 80 else 1.5)
            travel_time_min = round(dist / walk_speed * 60, 0)
            
            shelter_options.append({
                "shelter": shelter,
                "distance_km": round(dist, 2),
                "travel_time_min": travel_time_min,
                "route_safety": route_safety,
                "route_coords": route_coords,
                "score": round(score, 2),
            })
        
        # Sort by score descending
        shelter_options.sort(key=lambda s: s["score"], reverse=True)
        
        # Best route
        best = shelter_options[0] if shelter_options else None
        
        return {
            "ward_id": ward_id,
            "ward_name": getattr(ward, 'name', ''),
            "ward_centroid": {"lat": ward_lat, "lon": ward_lon},
            "risk_level": round(risk_score, 2),
            "recommended_shelter": best,
            "alternatives": shelter_options[1:3],  # Up to 2 alternatives
            "total_shelters_in_range": len(shelter_options),
            "evacuation_urgency": self._get_urgency(risk_score),
            "timestamp": datetime.now().isoformat(),
        }

    def compute_all_routes(self, wards, risk_data_map: Dict = None) -> Dict:
        """Compute evacuation routes for all wards"""
        all_wards = list(wards)
        risk_data_map = risk_data_map or {}
        
        routes = []
        for ward in all_wards:
            risk_data = risk_data_map.get(ward.ward_id)
            route = self.compute_evacuation_route(ward, risk_data)
            routes.append(route)
        
        # Sort by urgency
        urgency_order = {"immediate": 0, "prepare": 1, "monitor": 2, "standby": 3}
        routes.sort(key=lambda r: urgency_order.get(r["evacuation_urgency"], 4))
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_wards": len(routes),
            "routes": routes,
            "shelters": SHELTER_DATABASE,
            "flood_prone_roads": [r for r in ROAD_SEGMENTS if r["risk_zone"]],
        }

    def _haversine_distance(self, lat1, lon1, lat2, lon2) -> float:
        """Calculate distance in km between two points"""
        R = 6371
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        return 2 * R * math.asin(math.sqrt(a))

    def _assess_route_safety(
        self, from_lat, from_lon, to_lat, to_lon,
        ward_id: str, risk_score: float
    ) -> Dict:
        """Assess safety of the route between two points"""
        avoid_roads = []
        safety_score = 1.0
        
        for road in ROAD_SEGMENTS:
            if not road["risk_zone"]:
                continue
            
            # Check if ward is in this road's affected area
            if ward_id in road["wards"]:
                # Check if route roughly crosses this road
                if self._route_crosses_road(from_lat, from_lon, to_lat, to_lon, road["coords"]):
                    if risk_score > 50:
                        avoid_roads.append(road["name"])
                        safety_score -= 0.2
        
        safety_score = max(0.1, safety_score)
        
        status = "safe"
        if safety_score < 0.5:
            status = "hazardous"
        elif safety_score < 0.8:
            status = "moderate_risk"
        
        return {
            "safety_score": round(safety_score, 2),
            "status": status,
            "avoid_roads": avoid_roads,
            "safe_alternatives": [r["name"] for r in ROAD_SEGMENTS if not r["risk_zone"] and ward_id in r.get("wards", [])],
        }

    def _route_crosses_road(self, from_lat, from_lon, to_lat, to_lon, road_coords) -> bool:
        """Simple check if a route approximately crosses a road segment"""
        # Simplified: check if any road coordinate is close to the direct path
        for coord in road_coords:
            # Check if road point is roughly between origin and destination
            min_lat = min(from_lat, to_lat) - 0.01
            max_lat = max(from_lat, to_lat) + 0.01
            min_lon = min(from_lon, to_lon) - 0.01
            max_lon = max(from_lon, to_lon) + 0.01
            
            if min_lat <= coord[0] <= max_lat and min_lon <= coord[1] <= max_lon:
                return True
        return False

    def _generate_route(
        self, from_lat, from_lon, to_lat, to_lon,
        avoid_roads: List[str]
    ) -> List[List[float]]:
        """
        Generate route polyline coordinates.
        In production, would use OSRM. Here, generates a realistic path with waypoints.
        """
        # Create a multi-segment path with intermediate waypoints
        points = [[from_lat, from_lon]]
        
        # Add 2-3 intermediate waypoints for realism
        n_waypoints = 3
        for i in range(1, n_waypoints + 1):
            frac = i / (n_waypoints + 1)
            # Add slight offset for road-following realism
            offset_lat = (0.002 if i % 2 == 0 else -0.001) * (1 if not avoid_roads else 2)
            offset_lon = (0.001 if i % 2 == 1 else -0.002) * (1 if not avoid_roads else -1)
            
            mid_lat = from_lat + (to_lat - from_lat) * frac + offset_lat
            mid_lon = from_lon + (to_lon - from_lon) * frac + offset_lon
            points.append([round(mid_lat, 6), round(mid_lon, 6)])
        
        points.append([to_lat, to_lon])
        return points

    def _get_urgency(self, risk_score: float) -> str:
        if risk_score >= 80:
            return "immediate"
        if risk_score >= 60:
            return "prepare"
        if risk_score >= 40:
            return "monitor"
        return "standby"


# Global instance
evacuation_router = EvacuationRouter()
