"""
Configuration for external API keys and base URLs.

API keys are loaded from a .env file (falls back to environment variables).
Some APIs (Deezer, Open Library, Open-Meteo) are free and keyless.
"""

import os


# ── TMDB (Movies & TV) ───────────────────────────────────────────
# Free tier: ~40 requests/10s — get a key at https://www.themoviedb.org/settings/api
TMDB_API_KEY: str = os.getenv("TMDB_API_KEY", "")
TMDB_BASE_URL: str = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE: str = "https://image.tmdb.org/t/p/w500"

# ── Deezer (Music / Albums) ──────────────────────────────────────
# Completely free, no API key required
DEEZER_BASE_URL: str = "https://api.deezer.com"

# ── RAWG (Video Games) ───────────────────────────────────────────
# Free tier: 20,000 requests/month — get a key at https://rawg.io/apidocs
RAWG_API_KEY: str = os.getenv("RAWG_API_KEY", "")
RAWG_BASE_URL: str = "https://api.rawg.io/api"

# ── Open Library (Books) ─────────────────────────────────────────
# Completely free, no API key required
OPENLIBRARY_BASE_URL: str = "https://openlibrary.org"

# ── Open-Meteo (Locations / Weather / Timezone) ──────────────────
# Completely free, no API key required
GEOCODING_BASE_URL: str = "https://geocoding-api.open-meteo.com/v1"
WEATHER_BASE_URL: str = "https://api.open-meteo.com/v1"

# ── Unsplash (Location images) ────────────────────────────
# Free tier: 50 requests/hour — get a key at https://unsplash.com/developers
UNSPLASH_ACCESS_KEY: str = os.getenv("UNSPLASH_ACCESS_KEY", "")
UNSPLASH_BASE_URL: str = "https://api.unsplash.com"

# ── Shared HTTP settings ─────────────────────────────────────────
REQUEST_TIMEOUT: float = float(os.getenv("API_TIMEOUT", "15"))  # seconds
