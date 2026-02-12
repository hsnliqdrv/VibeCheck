"""
VibeCheck External API Services
================================

Provides async functions to fetch content from real third-party APIs,
returning data shaped to match the VibeCheck OpenAPI schemas.

Modules
-------
- **movies**    — TMDB API (requires TMDB_API_KEY env var)
- **albums**    — Deezer API (free, no key)
- **games**     — RAWG API (requires RAWG_API_KEY env var)
- **books**     — Open Library API (free, no key)
- **locations** — Open-Meteo Geocoding + Weather API (free, no key)

Usage
-----
>>> from external_apis import movies, albums, books
>>>
>>> results = await movies.search_movies("Inception")
>>> album   = await albums.get_album_by_id("103248")
>>> books_  = await books.search_books("Dune", author="Frank Herbert")
"""

from . import albums, books, games, locations, movies

__all__ = [
    "movies",
    "albums",
    "games",
    "books",
    "locations",
]
