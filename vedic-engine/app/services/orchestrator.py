"""Data Orchestrator — coordinates geocoding, chart fetching, and enrichment."""

import hashlib
import json
from datetime import datetime, timezone

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.services.ephemeris_fallback import build_chart_data, get_current_saturn_sign
from app.services.logic_engine import VedicLogicEngine
from app.utils.cache import Cache
from app.utils.logger import logger

settings = get_settings()
logic_engine = VedicLogicEngine()


class DataOrchestrator:
    def __init__(self, cache: Cache):
        self.cache = cache

    async def process(self, birth_input: dict) -> dict:
        """Full pipeline: geocode → chart → enrich → return."""
        # Check cache
        cache_key = self._cache_key(birth_input)
        cached = await self.cache.get_cached(cache_key)
        if cached:
            return cached

        # Step 1: Resolve location
        location = await self.resolve_location(
            birth_input["birth_city"], birth_input["birth_country"]
        )

        # Step 2: Get chart data
        chart_data = await self.get_vedic_chart(birth_input, location)

        # Step 3: Enrich with logic engine
        try:
            current_saturn = get_current_saturn_sign()
        except Exception:
            current_saturn = None

        # Build birth datetime for dasha calculation
        birth_dt = datetime.combine(
            birth_input["birth_date"], birth_input["birth_time"]
        )
        chart_data["birth_datetime"] = birth_dt.isoformat()

        enriched = logic_engine.enrich(
            chart_data,
            current_saturn_sign=current_saturn,
            reference_dt=datetime.now(timezone.utc).replace(tzinfo=None),
        )

        result = {
            "birth_input": birth_input,
            "location": location,
            "chart": chart_data,
            **enriched,
        }

        # Cache for 24 hours
        await self.cache.set_cached(cache_key, result, ttl=86400)
        return result

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
    async def resolve_location(self, city: str, country: str) -> dict:
        """Resolve city/country to lat/lng/timezone using geocoding API."""
        if settings.GEOCODING_API_KEY:
            try:
                return await self._call_geocoding_api(city, country)
            except Exception as e:
                logger.warning(f"Geocoding API failed: {e}")

        # Fallback: use a simple lookup for common cities
        return self._fallback_location(city, country)

    async def _call_geocoding_api(self, city: str, country: str) -> dict:
        """Call external geocoding API."""
        url = "https://api.timezonedb.com/v2.1/get-time-zone"
        params = {
            "key": settings.GEOCODING_API_KEY,
            "format": "json",
            "by": "zone",
            "zone": f"{country}/{city}",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            return {
                "latitude": data.get("lat", 0.0),
                "longitude": data.get("lng", 0.0),
                "timezone_id": data.get("zoneName", "UTC"),
                "utc_offset": data.get("gmtOffset", 0) / 3600,
                "dst_active": data.get("dst", "0") == "1",
            }

    def _fallback_location(self, city: str, country: str) -> dict:
        """Fallback location lookup for common cities."""
        locations = {
            "mumbai": {"latitude": 19.0760, "longitude": 72.8777, "timezone_id": "Asia/Kolkata", "utc_offset": 5.5},
            "delhi": {"latitude": 28.7041, "longitude": 77.1025, "timezone_id": "Asia/Kolkata", "utc_offset": 5.5},
            "new delhi": {"latitude": 28.6139, "longitude": 77.2090, "timezone_id": "Asia/Kolkata", "utc_offset": 5.5},
            "bangalore": {"latitude": 12.9716, "longitude": 77.5946, "timezone_id": "Asia/Kolkata", "utc_offset": 5.5},
            "chennai": {"latitude": 13.0827, "longitude": 80.2707, "timezone_id": "Asia/Kolkata", "utc_offset": 5.5},
            "kolkata": {"latitude": 22.5726, "longitude": 88.3639, "timezone_id": "Asia/Kolkata", "utc_offset": 5.5},
            "hyderabad": {"latitude": 17.3850, "longitude": 78.4867, "timezone_id": "Asia/Kolkata", "utc_offset": 5.5},
            "pune": {"latitude": 18.5204, "longitude": 73.8567, "timezone_id": "Asia/Kolkata", "utc_offset": 5.5},
            "jaipur": {"latitude": 26.9124, "longitude": 75.7873, "timezone_id": "Asia/Kolkata", "utc_offset": 5.5},
            "london": {"latitude": 51.5074, "longitude": -0.1278, "timezone_id": "Europe/London", "utc_offset": 0.0},
            "new york": {"latitude": 40.7128, "longitude": -74.0060, "timezone_id": "America/New_York", "utc_offset": -5.0},
            "los angeles": {"latitude": 34.0522, "longitude": -118.2437, "timezone_id": "America/Los_Angeles", "utc_offset": -8.0},
            "tokyo": {"latitude": 35.6762, "longitude": 139.6503, "timezone_id": "Asia/Tokyo", "utc_offset": 9.0},
            "sydney": {"latitude": -33.8688, "longitude": 151.2093, "timezone_id": "Australia/Sydney", "utc_offset": 10.0},
            "dubai": {"latitude": 25.2048, "longitude": 55.2708, "timezone_id": "Asia/Dubai", "utc_offset": 4.0},
            "singapore": {"latitude": 1.3521, "longitude": 103.8198, "timezone_id": "Asia/Singapore", "utc_offset": 8.0},
        }
        key = city.lower().strip()
        loc = locations.get(key, {
            "latitude": 28.6139,
            "longitude": 77.2090,
            "timezone_id": "Asia/Kolkata",
            "utc_offset": 5.5,
        })
        loc["dst_active"] = False
        return loc

    async def get_vedic_chart(self, birth_input: dict, location: dict) -> dict:
        """Get chart data from API or Swiss Ephemeris fallback."""
        if settings.ASTROLOGY_API_KEY:
            try:
                return await self._call_astrology_api(birth_input, location)
            except Exception as e:
                logger.warning(f"Astrology API failed, using Swiss Ephemeris: {e}")

        # Swiss Ephemeris fallback
        utc_dt = self._to_utc(birth_input, location)
        return build_chart_data(utc_dt, location["latitude"], location["longitude"])

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
    async def _call_astrology_api(self, birth_input: dict, location: dict) -> dict:
        """Call external astrology API for chart data."""
        # Placeholder — implement when specific API is chosen
        raise NotImplementedError("Configure ASTROLOGY_API_KEY for external chart API")

    def _to_utc(self, birth_input: dict, location: dict) -> datetime:
        """Convert local birth time to UTC."""
        local_dt = datetime.combine(birth_input["birth_date"], birth_input["birth_time"])
        utc_offset_hours = location.get("utc_offset", 0)
        from datetime import timedelta
        return local_dt - timedelta(hours=utc_offset_hours)

    def _cache_key(self, birth_input: dict) -> str:
        raw = json.dumps(
            {k: str(v) for k, v in birth_input.items()},
            sort_keys=True,
        )
        return f"vedic:reading:{hashlib.sha256(raw.encode()).hexdigest()}"
