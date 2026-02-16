"""
Weather API ingestion module
Fetches real-time weather data from Open-Meteo API (free, no API key required)
"""
import httpx
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from core.config import settings
from core.cache import get_cached_weather, cache_weather_data

logger = logging.getLogger(__name__)


class WeatherAPIClient:
    """Client for fetching weather data from Open-Meteo API"""
    
    def __init__(self):
        self.base_url = settings.WEATHER_API_URL
        self.client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=50)
        )
    
    async def get_forecast(
        self, 
        lat: float, 
        lon: float, 
        days: int = 3
    ) -> Optional[Dict[str, Any]]:
        """
        Get weather forecast for a location
        
        Args:
            lat: Latitude
            lon: Longitude
            days: Number of forecast days (default 3)
            
        Returns:
            Weather data dictionary or None if error
        """
        # Check cache first
        cached = get_cached_weather(lat, lon)
        if cached:
            logger.debug(f"Using cached weather data for ({lat}, {lon})")
            return cached
        
        try:
            params = {
                "latitude": lat,
                "longitude": lon,
                "hourly": [
                    "temperature_2m",
                    "relative_humidity_2m",
                    "rain",
                    "showers",
                    "precipitation",
                    "weather_code",
                    "cloud_cover",
                    "wind_speed_10m",
                    "wind_direction_10m"
                ],
                "daily": [
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "rain_sum",
                    "showers_sum",
                    "precipitation_sum"
                ],
                "timezone": "Asia/Kolkata",
                "forecast_days": days
            }
            
            logger.info(f"Fetching weather for ({lat:.4f}, {lon:.4f})")
            response = await self.client.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Cache the result
            cache_weather_data(lat, lon, data)
            
            return data
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching weather for ({lat}, {lon}): {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching weather for ({lat}, {lon}): {e}")
            return None
    
    async def get_forecast_batch(
        self, 
        locations: List[Dict[str, float]], 
        max_concurrent: int = 10
    ) -> Dict[str, Optional[Dict]]:
        """
        Fetch weather for multiple locations concurrently
        
        Args:
            locations: List of dicts with 'lat', 'lon', and optional 'id'
            max_concurrent: Maximum concurrent requests
            
        Returns:
            Dict mapping location id to weather data
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_with_limit(loc):
            async with semaphore:
                loc_id = loc.get('id', f"{loc['lat']}_{loc['lon']}")
                weather = await self.get_forecast(loc['lat'], loc['lon'])
                return loc_id, weather
        
        tasks = [fetch_with_limit(loc) for loc in locations]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        weather_data = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error in batch weather fetch: {result}")
                continue
            loc_id, weather = result
            weather_data[loc_id] = weather
        
        return weather_data
    
    def extract_rainfall_forecast(self, weather_data: Dict) -> Dict:
        """Extract rainfall forecast information"""
        if not weather_data:
            return {}
        
        hourly = weather_data.get("hourly", {})
        rain = hourly.get("rain", [])
        showers = hourly.get("showers", [])
        
        # Combine rain and showers
        total_precip = [r + s for r, s in zip(rain, showers)] if rain and showers else rain or showers
        
        return {
            "current_mm": total_precip[0] if total_precip else 0,
            "next_24h_mm": sum(total_precip[:24]) if len(total_precip) >= 24 else sum(total_precip),
            "next_48h_mm": sum(total_precip[:48]) if len(total_precip) >= 48 else sum(total_precip),
            "hourly_forecast": total_precip[:72]  # 72 hours
        }
    
    def extract_temperature_forecast(self, weather_data: Dict) -> Dict:
        """Extract temperature forecast information"""
        if not weather_data:
            return {}
        
        hourly = weather_data.get("hourly", {})
        temps = hourly.get("temperature_2m", [])
        
        if not temps:
            return {}
        
        current_temp = temps[0]
        max_temp_24h = max(temps[:24]) if len(temps) >= 24 else max(temps)
        max_temp_48h = max(temps[:48]) if len(temps) >= 48 else max(temps)
        
        # Calculate anomaly from seasonal average (Pune March ~30C)
        seasonal_avg = 30.0
        temp_anomaly = max(0, current_temp - seasonal_avg)
        
        return {
            "current_c": current_temp,
            "max_24h_c": max_temp_24h,
            "max_48h_c": max_temp_48h,
            "anomaly_c": temp_anomaly,
            "hourly_forecast": temps[:72]
        }
    
    def get_weather_summary(self, weather_data: Dict) -> Dict:
        """Get a summary of weather conditions"""
        rainfall = self.extract_rainfall_forecast(weather_data)
        temperature = self.extract_temperature_forecast(weather_data)
        
        # Determine weather condition
        condition = "clear"
        if rainfall.get("next_48h_mm", 0) > 100:
            condition = "heavy_rain"
        elif rainfall.get("next_48h_mm", 0) > 50:
            condition = "moderate_rain"
        elif rainfall.get("next_48h_mm", 0) > 20:
            condition = "light_rain"
        elif temperature.get("anomaly_c", 0) > 4:
            condition = "heatwave"
        elif temperature.get("anomaly_c", 0) > 2:
            condition = "hot"
        
        return {
            "condition": condition,
            "rainfall": rainfall,
            "temperature": temperature,
            "timestamp": datetime.now().isoformat()
        }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


class WeatherIngestionService:
    """Service for scheduled weather data ingestion"""
    
    def __init__(self):
        self.client = WeatherAPIClient()
    
    async def ingest_for_wards(self, wards: List[Any]) -> Dict:
        """
        Ingest weather data for all wards
        
        Args:
            wards: List of Ward objects
            
        Returns:
            Ingestion summary
        """
        locations = [
            {
                'id': ward.ward_id,
                'lat': ward.centroid_lat,
                'lon': ward.centroid_lon
            }
            for ward in wards
        ]
        
        logger.info(f"Starting weather ingestion for {len(locations)} wards")
        
        start_time = datetime.now()
        weather_data = await self.client.get_forecast_batch(locations)
        end_time = datetime.now()
        
        # Count successes and failures
        successes = sum(1 for v in weather_data.values() if v is not None)
        failures = len(weather_data) - successes
        
        summary = {
            "total_wards": len(wards),
            "successful": successes,
            "failed": failures,
            "duration_seconds": (end_time - start_time).total_seconds(),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Weather ingestion complete: {successes}/{len(wards)} successful")
        
        return summary
    
    async def close(self):
        """Close the service"""
        await self.client.close()
