"""
Weather service using Open-Meteo API (real data, no mock)
Supports: hourly rainfall, 7-day forecast, historical archive
"""
import httpx
import asyncio
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
import logging

from app.db.config import settings
from app.db.cache import cache_weather_data, get_cached_weather

logger = logging.getLogger(__name__)


class WeatherAPIClient:
    """
    Production Open-Meteo API client with:
    - Hourly current rainfall
    - 7-day forecast (rainfall + temperature)
    - Historical archive data
    - Redis caching (15 min TTL)
    - Async batch fetch for all ward centroids
    """

    def __init__(self):
        self.forecast_url = settings.WEATHER_API_URL
        self.archive_url = settings.WEATHER_ARCHIVE_URL
        self.forecast_days = settings.WEATHER_FORECAST_DAYS
        self.timeout = httpx.Timeout(30.0, connect=10.0)

    async def fetch_forecast(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Fetch forecast from Open-Meteo for a location
        Returns hourly data for next 7 days
        """
        # Check cache first
        cached = get_cached_weather(lat, lon)
        if cached:
            return cached

        params = {
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "hourly": ",".join([
                "temperature_2m",
                "relative_humidity_2m",
                "precipitation",
                "rain",
                "surface_pressure",
                "wind_speed_10m",
                "wind_gusts_10m",
            ]),
            "daily": ",".join([
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "rain_sum",
                "wind_speed_10m_max",
            ]),
            "timezone": "Asia/Kolkata",
            "forecast_days": self.forecast_days,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.forecast_url, params=params)
                response.raise_for_status()
                data = response.json()

                # Process and structure the response
                result = self._process_forecast(data, lat, lon)

                # Cache it
                cache_weather_data(lat, lon, result)

                return result

        except httpx.TimeoutException:
            logger.error(f"Weather API timeout for ({lat}, {lon})")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"Weather API HTTP error: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Weather API error for ({lat}, {lon}): {e}")
            return None

    async def fetch_historical(self, lat: float, lon: float, start_date: str, end_date: str) -> Optional[Dict]:
        """
        Fetch historical weather data from Open-Meteo Archive
        Used for ML training and historical analysis
        """
        params = {
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "start_date": start_date,
            "end_date": end_date,
            "daily": ",".join([
                "temperature_2m_max",
                "temperature_2m_min",
                "temperature_2m_mean",
                "precipitation_sum",
                "rain_sum",
                "wind_speed_10m_max",
            ]),
            "timezone": "Asia/Kolkata",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.archive_url, params=params)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Historical weather API error: {e}")
            return None

    def _process_forecast(self, data: Dict, lat: float, lon: float) -> Dict:
        """Process raw Open-Meteo response into structured forecast"""
        hourly = data.get("hourly", {})
        daily = data.get("daily", {})

        # Extract current conditions (first available hour)
        current_temp = None
        current_rainfall = None
        current_humidity = None
        current_wind = None

        temps = hourly.get("temperature_2m", [])
        precip = hourly.get("precipitation", [])
        humidity = hourly.get("relative_humidity_2m", [])
        wind = hourly.get("wind_speed_10m", [])

        if temps:
            # Find current hour index
            now = datetime.now()
            current_hour = now.hour
            idx = min(current_hour, len(temps) - 1)
            current_temp = temps[idx]
            current_rainfall = precip[idx] if idx < len(precip) else 0
            current_humidity = humidity[idx] if idx < len(humidity) else None
            current_wind = wind[idx] if idx < len(wind) else None

        # Calculate cumulative rainfall for next 48h
        rainfall_48h = sum(precip[:48]) if precip else 0

        # Calculate 7-day rainfall
        daily_rain = daily.get("precipitation_sum", [])
        rainfall_7d = sum(r for r in daily_rain if r is not None) if daily_rain else 0

        # Calculate max rainfall intensity (max hourly)
        max_rainfall_intensity = max(precip[:48]) if precip else 0

        # Temperature anomaly (current vs baseline)
        daily_max = daily.get("temperature_2m_max", [])
        daily_min = daily.get("temperature_2m_min", [])

        avg_temp_forecast = None
        if daily_max and daily_min:
            avg_max = sum(t for t in daily_max[:3] if t) / max(1, len([t for t in daily_max[:3] if t]))
            avg_min = sum(t for t in daily_min[:3] if t) / max(1, len([t for t in daily_min[:3] if t]))
            avg_temp_forecast = (avg_max + avg_min) / 2

        # Weather condition classification
        condition = self._classify_weather(current_rainfall, current_temp, max_rainfall_intensity)

        result = {
            "location": {"lat": lat, "lon": lon},
            "fetched_at": datetime.now().isoformat(),
            "current": {
                "temperature_c": current_temp,
                "rainfall_mm": current_rainfall,
                "humidity_pct": current_humidity,
                "wind_speed_kmh": current_wind,
                "condition": condition,
            },
            "forecast": {
                "rainfall_48h_mm": round(rainfall_48h, 2),
                "rainfall_7d_mm": round(rainfall_7d, 2),
                "max_rainfall_intensity_mm_h": round(max_rainfall_intensity, 2),
                "avg_temp_forecast_c": round(avg_temp_forecast, 1) if avg_temp_forecast else None,
            },
            "hourly": {
                "temperature_2m": temps[:48] if temps else [],
                "precipitation": precip[:48] if precip else [],
                "humidity": humidity[:48] if humidity else [],
                "wind_speed": wind[:48] if wind else [],
            },
            "daily": {
                "precipitation_sum": daily_rain,
                "temperature_max": daily_max,
                "temperature_min": daily_min,
            },
        }

        return result

    def _classify_weather(self, rainfall: float, temp: float, intensity: float) -> str:
        """Classify current weather condition"""
        if rainfall is None:
            return "unknown"
        if intensity > 50:
            return "heavy_rain"
        if intensity > 20:
            return "moderate_rain"
        if rainfall > 0.5:
            return "light_rain"
        if temp and temp > 42:
            return "extreme_heat"
        if temp and temp > 38:
            return "heatwave"
        if temp and temp > 35:
            return "hot"
        return "clear"


class WeatherIngestionService:
    """Batch weather ingestion for all wards"""

    def __init__(self):
        self.client = WeatherAPIClient()
        self.max_concurrent = 5

    async def ingest_for_wards(self, wards) -> Dict[str, Any]:
        """Fetch weather for all wards with rate limiting"""
        results = {"success": 0, "failed": 0, "cached": 0, "wards": {}}
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def fetch_one(ward):
            async with semaphore:
                try:
                    data = await self.client.fetch_forecast(
                        ward.centroid_lat, ward.centroid_lon
                    )
                    if data:
                        results["success"] += 1
                        results["wards"][ward.ward_id] = data
                    else:
                        results["failed"] += 1
                except Exception as e:
                    logger.error(f"Ward {ward.ward_id} weather fetch failed: {e}")
                    results["failed"] += 1

        tasks = [fetch_one(ward) for ward in wards]
        await asyncio.gather(*tasks)

        logger.info(f"Weather ingestion: {results['success']} success, {results['failed']} failed")
        return results

    async def fetch_historical_for_training(
        self, lat: float, lon: float, years_back: int = 5
    ) -> Optional[Dict]:
        """Fetch multi-year historical data for ML training"""
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365 * years_back)).strftime("%Y-%m-%d")

        return await self.client.fetch_historical(lat, lon, start_date, end_date)
