"""
Movies & TV service — powered by the TMDB API.

API docs: https://developer.themoviedb.org/docs
Free tier: ~40 requests / 10 seconds.
Requires TMDB_API_KEY environment variable.

Returns data shaped to the VibeCheck Movie schema:
    id, title, year, director, poster, season, episode, type, url
"""

from __future__ import annotations

from typing import Any

from .base import fetch_json
from .config import TMDB_API_KEY, TMDB_BASE_URL, TMDB_IMAGE_BASE


def _normalize_movie(raw: dict[str, Any], *, media_type: str = "movie") -> dict[str, Any]:
    """Map a TMDB result to the VibeCheck Movie schema."""
    tmdb_id = raw.get("id", "")
    is_tv = media_type == "tv" or "first_air_date" in raw

    title = raw.get("title") or raw.get("name", "")
    date_str = raw.get("release_date") or raw.get("first_air_date", "")
    year = _parse_year(date_str)

    poster_path = raw.get("poster_path")
    poster = f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else None

    # Director is only available in detail responses (credits)
    director = raw.get("_director", "N/A")

    return {
        "id": str(tmdb_id),
        "title": title,
        "year": year,
        "director": director,
        "poster": poster,
        "season": raw.get("number_of_seasons"),
        "episode": raw.get("number_of_episodes"),
        "type": "tv" if is_tv else "movie",
        "url": (
            f"https://www.themoviedb.org/{'tv' if is_tv else 'movie'}/{tmdb_id}"
            if tmdb_id
            else None
        ),
    }


def _parse_year(date_str: str) -> int:
    """Extract a 4-digit year from a TMDB date string like '2019-07-02'."""
    try:
        return int(date_str[:4])
    except (ValueError, TypeError, IndexError):
        return 0


# ── Public API ────────────────────────────────────────────────────


async def search_movies(
    query: str,
    *,
    year: int | None = None,
    type_filter: str | None = None,  # "movie" | "tv"
    limit: int = 20,
    offset: int = 0,
) -> dict[str, Any]:
    """
    Search movies/TV shows by title.

    Args:
        limit: Maximum number of results to return (contract default: 20).
        offset: Pagination offset.

    Returns:
        {
            "data": [Movie, ...],
            "total": int,
            "limit": int,
            "offset": int,
        }
    """
    if not TMDB_API_KEY:
        raise RuntimeError("TMDB_API_KEY environment variable is not set")

    # TMDB uses page-based pagination (20 per page); convert offset → page
    page = (offset // 20) + 1

    # Choose endpoint based on type filter
    if type_filter == "tv":
        endpoint = f"{TMDB_BASE_URL}/search/tv"
    elif type_filter == "movie":
        endpoint = f"{TMDB_BASE_URL}/search/movie"
    else:
        endpoint = f"{TMDB_BASE_URL}/search/multi"

    params: dict[str, Any] = {
        "api_key": TMDB_API_KEY,
        "query": query,
        "page": page,
        "include_adult": "false",
    }
    if year:
        if type_filter == "tv":
            params["first_air_date_year"] = year
        else:
            params["year"] = year

    raw = await fetch_json(endpoint, params=params)

    results = raw.get("results", [])
    # For multi-search, filter out person results
    if not type_filter:
        results = [r for r in results if r.get("media_type") in ("movie", "tv")]

    movies = [
        _normalize_movie(r, media_type=r.get("media_type", type_filter or "movie"))
        for r in results
    ]

    # Apply limit (TMDB always returns up to 20; trim if caller wants fewer)
    movies = movies[:limit]
    total = raw.get("total_results", len(movies))

    return {
        "data": movies,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


async def get_movie_by_id(
    movie_id: str, *, media_type: str = "movie"
) -> dict[str, Any] | None:
    """
    Get detailed movie/TV info by TMDB ID.

    Args:
        movie_id: The TMDB numeric ID.
        media_type: "movie" or "tv".

    Returns a Movie dict or None if not found.
    """
    if not TMDB_API_KEY:
        raise RuntimeError("TMDB_API_KEY environment variable is not set")

    endpoint = f"{TMDB_BASE_URL}/{media_type}/{movie_id}"
    params: dict[str, Any] = {
        "api_key": TMDB_API_KEY,
        "append_to_response": "credits",
    }

    try:
        raw = await fetch_json(endpoint, params=params)
    except Exception:
        return None

    if not raw or raw.get("success") is False:
        return None

    # Extract director from credits
    credits = raw.get("credits", {})
    crew = credits.get("crew", [])
    director = next(
        (p.get("name", "N/A") for p in crew if p.get("job") == "Director"),
        "N/A",
    )
    raw["_director"] = director

    return _normalize_movie(raw, media_type=media_type)
