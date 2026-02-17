"""
OSM Infrastructure Service using Overpass API
Fetches real infrastructure data: hospitals, fire stations, shelters, road density
"""
import httpx
import asyncio
import math
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from app.db.config import settings
from app.db.cache import cache_osm_data, get_cached_osm

logger = logging.getLogger(__name__)


class OSMService:
    """
    OpenStreetMap Overpass API integration for infrastructure data
    
    Queries:
    - Hospitals and clinics
    - Fire stations
    - Emergency shelters + schools (can serve as shelters)
    - Road network density
    
    Results are aggregated per ward using centroid-radius spatial join
    """

    def __init__(self):
        self.overpass_url = settings.OVERPASS_API_URL
        self.timeout = httpx.Timeout(60.0, connect=15.0)

    async def fetch_ward_infrastructure(self, ward_id: str, lat: float, lon: float,
                                          radius_m: int = 2000) -> Dict:
        """
        Fetch all infrastructure within radius of ward centroid
        Returns aggregated counts and density scores
        """
        # Check cache first
        cached = get_cached_osm(ward_id)
        if cached:
            return cached

        result = {
            "ward_id": ward_id,
            "fetched_at": datetime.now().isoformat(),
            "hospitals": 0,
            "clinics": 0,
            "fire_stations": 0,
            "police_stations": 0,
            "shelters": 0,
            "schools": 0,
            "road_length_km": 0.0,
            "road_density_km_per_sqkm": 0.0,
            "infrastructure_density": 0.0,
            "source": "osm_overpass",
        }

        try:
            # Fetch medical facilities
            medical = await self._query_amenities(lat, lon, radius_m,
                                                     ["hospital", "clinic", "doctors"])
            result["hospitals"] = sum(1 for f in medical if f["type"] == "hospital")
            result["clinics"] = sum(1 for f in medical if f["type"] in ["clinic", "doctors"])

            # Fetch emergency services
            emergency = await self._query_amenities(lat, lon, radius_m,
                                                      ["fire_station", "police"])
            result["fire_stations"] = sum(1 for f in emergency if f["type"] == "fire_station")
            result["police_stations"] = sum(1 for f in emergency if f["type"] == "police")

            # Fetch shelters + schools
            shelters = await self._query_amenities(lat, lon, radius_m,
                                                     ["shelter", "school", "community_centre"])
            result["shelters"] = sum(1 for f in shelters if f["type"] in ["shelter", "community_centre"])
            result["schools"] = sum(1 for f in shelters if f["type"] == "school")

            # Fetch road network
            road_km = await self._query_road_density(lat, lon, radius_m)
            area_sqkm = math.pi * (radius_m / 1000) ** 2
            result["road_length_km"] = round(road_km, 2)
            result["road_density_km_per_sqkm"] = round(road_km / area_sqkm, 2) if area_sqkm > 0 else 0

            # Compute infrastructure density score (0-10)
            result["infrastructure_density"] = self._compute_density_score(result)

            # Cache results
            cache_osm_data(ward_id, result)

            return result

        except Exception as e:
            logger.error(f"OSM fetch failed for ward {ward_id}: {e}")
            return result

    async def _query_amenities(self, lat: float, lon: float, radius_m: int,
                                amenity_types: List[str]) -> List[Dict]:
        """Query Overpass API for amenities near a point"""
        amenity_filter = "|".join(amenity_types)
        query = f"""
        [out:json][timeout:25];
        (
          node["amenity"~"{amenity_filter}"](around:{radius_m},{lat},{lon});
          way["amenity"~"{amenity_filter}"](around:{radius_m},{lat},{lon});
        );
        out center;
        """

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.overpass_url, data={"data": query})
                response.raise_for_status()
                data = response.json()

                features = []
                for element in data.get("elements", []):
                    tags = element.get("tags", {})
                    feature = {
                        "type": tags.get("amenity", "unknown"),
                        "name": tags.get("name", "Unnamed"),
                        "lat": element.get("lat") or element.get("center", {}).get("lat"),
                        "lon": element.get("lon") or element.get("center", {}).get("lon"),
                    }
                    features.append(feature)

                return features

        except Exception as e:
            logger.error(f"Overpass amenity query failed: {e}")
            return []

    async def _query_road_density(self, lat: float, lon: float, radius_m: int) -> float:
        """Query total road length (km) within radius"""
        query = f"""
        [out:json][timeout:25];
        way["highway"~"primary|secondary|tertiary|residential|trunk"](around:{radius_m},{lat},{lon});
        out geom;
        """

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.overpass_url, data={"data": query})
                response.raise_for_status()
                data = response.json()

                total_length_km = 0.0
                for element in data.get("elements", []):
                    if "geometry" in element:
                        coords = element["geometry"]
                        for i in range(len(coords) - 1):
                            total_length_km += self._haversine_km(
                                coords[i]["lat"], coords[i]["lon"],
                                coords[i + 1]["lat"], coords[i + 1]["lon"]
                            )

                return total_length_km

        except Exception as e:
            logger.error(f"Overpass road query failed: {e}")
            return 0.0

    def _compute_density_score(self, infra: Dict) -> float:
        """
        Compute infrastructure density score (0-10)
        Higher = more infrastructure = less vulnerable
        """
        score = 0.0
        score += min(3.0, infra["hospitals"] * 1.0 + infra["clinics"] * 0.3)
        score += min(2.0, infra["fire_stations"] * 1.5 + infra["police_stations"] * 0.5)
        score += min(2.0, infra["shelters"] * 0.5 + infra["schools"] * 0.2)
        score += min(3.0, infra["road_density_km_per_sqkm"] * 0.3)
        return round(min(10, score), 2)

    @staticmethod
    def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine distance in kilometers"""
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    async def batch_fetch_all_wards(self, wards) -> Dict[str, Dict]:
        """Fetch infrastructure for all wards with rate limiting"""
        results = {}
        semaphore = asyncio.Semaphore(2)  # Overpass API is rate-limited

        async def fetch_one(ward):
            async with semaphore:
                await asyncio.sleep(1)  # Rate limit: 1 req/sec
                data = await self.fetch_ward_infrastructure(
                    ward.ward_id, ward.centroid_lat, ward.centroid_lon
                )
                results[ward.ward_id] = data

        tasks = [fetch_one(ward) for ward in wards]
        await asyncio.gather(*tasks)

        logger.info(f"OSM infrastructure fetched for {len(results)} wards")
        return results


# Global instance
osm_service = OSMService()
