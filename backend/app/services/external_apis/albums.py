"""
Albums service — powered by the Deezer API.

API docs: https://developers.deezer.com/api
Completely free, no API key required.

Returns data shaped to the VibeCheck Album schema:
    id, title, artist, cover, duration (seconds), url
"""

from __future__ import annotations

from typing import Any

from .base import fetch_json
from .config import DEEZER_BASE_URL


def _normalize_album(raw: dict[str, Any]) -> dict[str, Any]:
    """Map a Deezer album object to the VibeCheck Album schema."""
    artist = raw.get("artist", {})
    return {
        "id": str(raw.get("id", "")),
        "title": raw.get("title", ""),
        "artist": artist.get("name", "") if isinstance(artist, dict) else str(artist),
        "cover": raw.get("cover_big") or raw.get("cover_medium") or raw.get("cover"),
        "duration": raw.get("duration"),  # Deezer returns duration in seconds
        "url": raw.get("link"),
    }


def _normalize_album_detail(raw: dict[str, Any]) -> dict[str, Any]:
    """Map a Deezer album detail response (includes total duration from tracks)."""
    album = _normalize_album(raw)
    # Sum track durations if the top-level duration is missing
    if not album["duration"] and "tracks" in raw:
        tracks = raw["tracks"].get("data", [])
        album["duration"] = sum(t.get("duration", 0) for t in tracks)
    return album


# ── Public API ────────────────────────────────────────────────────


async def search_albums(
    query: str,
    *,
    artist: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict[str, Any]:
    """
    Search albums by title or artist.

    Returns:
        {
            "data": [Album, ...],
            "total": int,
            "limit": int,
            "offset": int,
        }
    """
    search_term = f'artist:"{artist}" {query}'.strip() if artist else query

    raw = await fetch_json(
        f"{DEEZER_BASE_URL}/search/album",
        params={"q": search_term, "limit": limit, "index": offset},
    )

    albums = [_normalize_album(a) for a in raw.get("data", [])]

    return {
        "data": albums,
        "total": raw.get("total", len(albums)),
        "limit": limit,
        "offset": offset,
    }


async def get_album_by_id(album_id: str) -> dict[str, Any] | None:
    """
    Get detailed album info by Deezer album ID.

    Returns an Album dict or None if not found.
    """
    try:
        raw = await fetch_json(f"{DEEZER_BASE_URL}/album/{album_id}")
    except Exception:
        return None

    if raw.get("error"):
        return None

    return _normalize_album_detail(raw)
