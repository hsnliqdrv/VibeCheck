"""
Games service — powered by the RAWG API.

API docs: https://rawg.io/apidocs
Free tier: 20,000 requests / month.
Requires RAWG_API_KEY environment variable.

Returns data shaped to the VibeCheck Game schema:
    id, title, platform, cover, difficulty (Easy|Medium|Hard), url
"""

from __future__ import annotations

from typing import Any

from .base import fetch_json
from .config import RAWG_API_KEY, RAWG_BASE_URL


def _normalize_game(raw: dict[str, Any]) -> dict[str, Any]:
    """Map a RAWG game object to the VibeCheck Game schema."""
    platforms = raw.get("platforms") or []
    # Pick the first platform name (RAWG returns [{platform: {name:...}}, ...])
    platform_name = ""
    if platforms:
        first = platforms[0]
        if isinstance(first, dict):
            platform_name = first.get("platform", {}).get("name", "")

    return {
        "id": str(raw.get("id", "")),
        "title": raw.get("name", ""),
        "platform": platform_name,
        "cover": raw.get("background_image"),
        "difficulty": _estimate_difficulty(raw),
        "url": f"https://rawg.io/games/{raw.get('slug', '')}",
    }


def _estimate_difficulty(raw: dict[str, Any]) -> str | None:
    """
    RAWG doesn't provide a difficulty field, so we estimate from playtime.
    - < 10 hours average → Easy
    - 10-30 hours → Medium
    - > 30 hours → Hard
    Returns None if playtime data is unavailable.
    """
    playtime = raw.get("playtime")  # average playtime in hours
    if not playtime:
        return None
    if playtime < 10:
        return "Easy"
    if playtime <= 30:
        return "Medium"
    return "Hard"


# ── Public API ────────────────────────────────────────────────────


async def search_games(
    query: str,
    *,
    platform: str | None = None,
    difficulty: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict[str, Any]:
    """
    Search games by title, optionally filtered by platform or difficulty.

    Note: Difficulty filtering is done client-side since RAWG has no
    difficulty param. We fetch extra results and filter down.

    Returns:
        {
            "data": [Game, ...],
            "total": int,
            "limit": int,
            "offset": int,
        }
    """
    if not RAWG_API_KEY:
        raise RuntimeError("RAWG_API_KEY environment variable is not set")

    page = (offset // limit) + 1

    params: dict[str, Any] = {
        "key": RAWG_API_KEY,
        "search": query,
        "page_size": limit if not difficulty else limit * 2,  # over-fetch for filtering
        "page": page,
    }
    if platform:
        params["search"] = f"{query} {platform}"

    raw = await fetch_json(f"{RAWG_BASE_URL}/games", params=params)

    games = [_normalize_game(g) for g in raw.get("results", [])]

    # Client-side difficulty filter
    if difficulty:
        games = [g for g in games if g.get("difficulty") == difficulty]
        games = games[:limit]

    return {
        "data": games,
        "total": raw.get("count", len(games)),
        "limit": limit,
        "offset": offset,
    }


async def get_game_by_id(game_id: str) -> dict[str, Any] | None:
    """
    Get detailed game info by RAWG game ID.

    Returns a Game dict or None if not found.
    """
    if not RAWG_API_KEY:
        raise RuntimeError("RAWG_API_KEY environment variable is not set")

    try:
        raw = await fetch_json(
            f"{RAWG_BASE_URL}/games/{game_id}",
            params={"key": RAWG_API_KEY},
        )
    except Exception:
        return None

    if raw.get("detail") == "Not found.":
        return None

    return _normalize_game(raw)
