"""Startup content seeding for all five discovery categories."""

import asyncio
from typing import Any

from app.models.content import Album, Book, Game, GameDifficulty, Location, Movie, MovieType
from app.services.external_apis import albums, books, games, locations, movies


SEED_QUERIES = {
    "movies": ["popular", "inception", "interstellar", "matrix"],
    "albums": ["top hits", "billie eilish", "coldplay", "adele"],
    "games": ["mario", "zelda", "fifa", "minecraft"],
    "books": ["harry potter", "dune", "atomic habits", "hobbit"],
    "locations": ["tokyo", "paris", "new york", "istanbul"],
}


async def _fetch_unique_items(search_fn, queries: list[str], target_count: int) -> list[dict[str, Any]]:
    """Fetch unique items by id from multiple search terms until target_count is reached."""
    collected: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for query in queries:
        if len(collected) >= target_count:
            break

        try:
            result = await search_fn(query, limit=max(10, target_count * 2), offset=0)
        except Exception as exc:
            print(f"[seed_content] Failed query '{query}': {exc}")
            continue

        for item in result.get("data", []):
            item_id = str(item.get("id", "")).strip()
            if not item_id or item_id in seen_ids:
                continue

            seen_ids.add(item_id)
            collected.append(item)

            if len(collected) >= target_count:
                break

    return collected[:target_count]


async def _fetch_all_categories(items_per_category: int) -> dict[str, list[dict[str, Any]]]:
    """Fetch seed payloads for all five content categories."""
    return {
        "movies": await _fetch_unique_items(movies.search_movies, SEED_QUERIES["movies"], items_per_category),
        "albums": await _fetch_unique_items(albums.search_albums, SEED_QUERIES["albums"], items_per_category),
        "games": await _fetch_unique_items(games.search_games, SEED_QUERIES["games"], items_per_category),
        "books": await _fetch_unique_items(books.search_books, SEED_QUERIES["books"], items_per_category),
        "locations": await _fetch_unique_items(locations.search_locations, SEED_QUERIES["locations"], items_per_category),
    }


def _upsert_movie(db, payload: dict[str, Any]) -> None:
    existing = db.query(Movie).filter_by(id=payload["id"]).first()
    if isinstance(payload.get("type"), str):
        payload["type"] = MovieType(payload["type"])
    if existing:
        for key, value in payload.items():
            setattr(existing, key, value)
    else:
        db.add(Movie(**payload))


def _upsert_album(db, payload: dict[str, Any]) -> None:
    existing = db.query(Album).filter_by(id=payload["id"]).first()
    if existing:
        for key, value in payload.items():
            setattr(existing, key, value)
    else:
        db.add(Album(**payload))


def _upsert_game(db, payload: dict[str, Any]) -> None:
    existing = db.query(Game).filter_by(id=payload["id"]).first()
    if payload.get("difficulty") and isinstance(payload.get("difficulty"), str):
        payload["difficulty"] = GameDifficulty(payload["difficulty"])
    if existing:
        for key, value in payload.items():
            setattr(existing, key, value)
    else:
        db.add(Game(**payload))


def _upsert_book(db, payload: dict[str, Any]) -> None:
    if "totalPages" in payload:
        payload["total_pages"] = payload.pop("totalPages")
    existing = db.query(Book).filter_by(id=payload["id"]).first()
    if existing:
        for key, value in payload.items():
            setattr(existing, key, value)
    else:
        db.add(Book(**payload))


def _upsert_location(db, payload: dict[str, Any]) -> None:
    existing = db.query(Location).filter_by(id=payload["id"]).first()
    if existing:
        for key, value in payload.items():
            setattr(existing, key, value)
    else:
        db.add(Location(**payload))


def seed_startup_content(db, items_per_category: int = 5) -> None:
    """Fetch and persist startup content for all categories."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        payloads = loop.run_until_complete(_fetch_all_categories(items_per_category))
    finally:
        loop.close()
        asyncio.set_event_loop(None)

    saved_counts = {"movies": 0, "albums": 0, "games": 0, "books": 0, "locations": 0}

    for movie_payload in payloads["movies"]:
        try:
            _upsert_movie(db, movie_payload)
            saved_counts["movies"] += 1
        except Exception as exc:
            print(f"[seed_content] Failed to save movie {movie_payload.get('id')}: {exc}")

    for album_payload in payloads["albums"]:
        try:
            _upsert_album(db, album_payload)
            saved_counts["albums"] += 1
        except Exception as exc:
            print(f"[seed_content] Failed to save album {album_payload.get('id')}: {exc}")

    for game_payload in payloads["games"]:
        try:
            _upsert_game(db, game_payload)
            saved_counts["games"] += 1
        except Exception as exc:
            print(f"[seed_content] Failed to save game {game_payload.get('id')}: {exc}")

    for book_payload in payloads["books"]:
        try:
            _upsert_book(db, book_payload)
            saved_counts["books"] += 1
        except Exception as exc:
            print(f"[seed_content] Failed to save book {book_payload.get('id')}: {exc}")

    for location_payload in payloads["locations"]:
        try:
            _upsert_location(db, location_payload)
            saved_counts["locations"] += 1
        except Exception as exc:
            print(f"[seed_content] Failed to save location {location_payload.get('id')}: {exc}")

    db.commit()
    print(
        "[seed_content] Seeded startup content: "
        f"movies={saved_counts['movies']}, albums={saved_counts['albums']}, "
        f"games={saved_counts['games']}, books={saved_counts['books']}, "
        f"locations={saved_counts['locations']}"
    )
