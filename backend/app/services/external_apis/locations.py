"""
Locations / Travel service — powered by Open-Meteo Geocoding + Weather APIs.

API docs:
  - Geocoding: https://open-meteo.com/en/docs/geocoding-api
  - Weather:   https://open-meteo.com/en/docs

Completely free, no API key required.

Returns data shaped to the VibeCheck Location schema:
    id, name, city, country, image, weather, temperature, timezone, url
"""

from __future__ import annotations

import asyncio
import re
from typing import Any

import httpx

from .base import fetch_json
from .config import GEOCODING_BASE_URL, UNSPLASH_ACCESS_KEY, UNSPLASH_BASE_URL, WEATHER_BASE_URL


def _normalize_location(raw: dict[str, Any]) -> dict[str, Any]:
    """Map an Open-Meteo geocoding result + weather to VibeCheck Location schema."""
    loc_id = str(raw.get("id", ""))
    name = raw.get("name", "")
    country = raw.get("country", "")
    admin1 = raw.get("admin1", "")  # state / region

    return {
        "id": loc_id,
        "name": name,
        "city": name,
        "country": country,
        "image": None,  # Open-Meteo doesn't provide images
        "weather": None,  # filled in by _enrich_with_weather
        "temperature": None,
        "timezone": raw.get("timezone"),
        "url": (
            f"https://www.google.com/maps/@{raw.get('latitude')},{raw.get('longitude')},12z"
            if raw.get("latitude")
            else None
        ),
        # internal — used for weather enrichment, stripped before return
        "_lat": raw.get("latitude"),
        "_lon": raw.get("longitude"),
    }


async def _get_location_image(name: str) -> str | None:
    """Return a location photo URL from Unsplash search API."""
    if not UNSPLASH_ACCESS_KEY:
        return None
    try:
        data = await fetch_json(
            f"{UNSPLASH_BASE_URL}/search/photos",
            params={
                "query": f"{name} city landscape",
                "per_page": 1,
                "orientation": "landscape",
            },
            headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
        )
        results = data.get("results", [])
        if results:
            return results[0].get("urls", {}).get("regular")
    except Exception:
        pass
    return None


async def _enrich_with_weather(location: dict[str, Any]) -> dict[str, Any]:
    """Fetch current weather and a photo for the location."""
    lat, lon = location.pop("_lat", None), location.pop("_lon", None)
    name = location.get("name", "")

    try:
        async def _fetch_weather() -> dict | None:
            if lat is None or lon is None:
                return None
            try:
                return await fetch_json(
                    f"{WEATHER_BASE_URL}/forecast",
                    params={
                        "latitude": lat,
                        "longitude": lon,
                        "current_weather": "true",
                        "timezone": "auto",
                    },
                )
            except Exception:
                return None

        # Fetch weather and image in parallel (both best-effort)
        results = await asyncio.gather(
            _fetch_weather(), _get_location_image(name),
            return_exceptions=True,
        )

        weather_raw = results[0] if isinstance(results[0], dict) else None
        image_url = results[1] if isinstance(results[1], str) else None

        if weather_raw:
            current = weather_raw.get("current_weather", {})
            location["temperature"] = current.get("temperature")
            location["weather"] = _wmo_to_description(current.get("weathercode"))
            location["timezone"] = weather_raw.get("timezone", location.get("timezone"))

        if image_url:
            location["image"] = image_url
    except Exception:
        pass  # enrichment is best-effort

    return location


def _wmo_to_description(code: int | None) -> str:
    """Convert WMO weather interpretation code to a human-readable string."""
    if code is None:
        return "Unknown"
    mapping = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow fall",
        73: "Moderate snow fall",
        75: "Heavy snow fall",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }
    return mapping.get(code, "Unknown")


# ── Public API ────────────────────────────────────────────────────


async def search_locations(
    query: str,
    *,
    country: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict[str, Any]:
    """
    Search cities / destinations by name, optionally filtered by country.

    Each result is enriched with live weather and timezone data.

    Returns:
        {
            "data": [Location, ...],
            "total": int,
            "limit": int,
            "offset": int,
        }
    """
    params: dict[str, Any] = {
        "name": query,
        "count": min(limit, 100),  # API max is 100
        "language": "en",
        "format": "json",
    }

    raw = await fetch_json(f"{GEOCODING_BASE_URL}/search", params=params)

    results = raw.get("results", [])

    # Country filter (Open-Meteo doesn't have a country parameter)
    if country:
        country_lower = country.lower()
        results = [
            r
            for r in results
            if country_lower in (r.get("country", "").lower())
            or country_lower in (r.get("country_code", "").lower())
        ]

    # Apply offset (API doesn't support pagination natively)
    total = len(results)
    results = results[offset : offset + limit]

    locations = [_normalize_location(r) for r in results]

    # Enrich each location with live weather
    enriched = []
    for loc in locations:
        enriched.append(await _enrich_with_weather(loc))

    return {
        "data": enriched,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


async def get_location_by_id(location_id: str) -> dict[str, Any] | None:
    """
    Get location details by Open-Meteo geocoding ID.

    Uses the Open-Meteo get_by_id endpoint for direct lookup.

    Returns a Location dict or None if not found.
    """
    try:
        raw = await fetch_json(
            f"{GEOCODING_BASE_URL}/get",
            params={"id": int(location_id)},
        )
    except (ValueError, TypeError):
        return None
    except Exception:
        return None

    if not raw or raw.get("error"):
        return None

    loc = _normalize_location(raw)
    return await _enrich_with_weather(loc)
