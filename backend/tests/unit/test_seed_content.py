"""
Unit tests for startup content seeding.

Usage (from backend directory):
    pytest tests/unit/test_seed_content.py -v

Optional explicit backend path (otherwise current directory is used):
    BACKEND_PATH=/absolute/path/to/backend pytest tests/unit/test_seed_content.py -v
"""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

backend_root = Path(os.getenv("BACKEND_PATH", Path.cwd())).resolve()
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app import seed_content


def test_seed_startup_content_saves_five_per_category(monkeypatch):
    async def fake_fetch_all_categories(items_per_category):
        assert items_per_category == 5
        return {
            "movies": [{"id": f"m{i}"} for i in range(5)],
            "albums": [{"id": f"a{i}"} for i in range(5)],
            "games": [{"id": f"g{i}"} for i in range(5)],
            "books": [{"id": f"b{i}"} for i in range(5)],
            "locations": [{"id": f"l{i}"} for i in range(5)],
        }

    movie_upsert = MagicMock()
    album_upsert = MagicMock()
    game_upsert = MagicMock()
    book_upsert = MagicMock()
    location_upsert = MagicMock()

    monkeypatch.setattr(seed_content, "_fetch_all_categories", fake_fetch_all_categories)
    monkeypatch.setattr(seed_content, "_upsert_movie", movie_upsert)
    monkeypatch.setattr(seed_content, "_upsert_album", album_upsert)
    monkeypatch.setattr(seed_content, "_upsert_game", game_upsert)
    monkeypatch.setattr(seed_content, "_upsert_book", book_upsert)
    monkeypatch.setattr(seed_content, "_upsert_location", location_upsert)

    db = MagicMock()

    seed_content.seed_startup_content(db, items_per_category=5)

    assert movie_upsert.call_count == 5
    assert album_upsert.call_count == 5
    assert game_upsert.call_count == 5
    assert book_upsert.call_count == 5
    assert location_upsert.call_count == 5
    db.commit.assert_called_once()


def test_fetch_all_categories_calls_all_five_searches(monkeypatch):
    calls = []

    async def fake_movies(query, limit, offset):
        calls.append(("movies", query, limit, offset))
        return {"data": [{"id": "movie-1"}]}

    async def fake_albums(query, limit, offset):
        calls.append(("albums", query, limit, offset))
        return {"data": [{"id": "album-1"}]}

    async def fake_games(query, limit, offset):
        calls.append(("games", query, limit, offset))
        return {"data": [{"id": "game-1"}]}

    async def fake_books(query, limit, offset):
        calls.append(("books", query, limit, offset))
        return {"data": [{"id": "book-1"}]}

    async def fake_locations(query, limit, offset):
        calls.append(("locations", query, limit, offset))
        return {"data": [{"id": "location-1"}]}

    monkeypatch.setattr(seed_content.movies, "search_movies", fake_movies)
    monkeypatch.setattr(seed_content.albums, "search_albums", fake_albums)
    monkeypatch.setattr(seed_content.games, "search_games", fake_games)
    monkeypatch.setattr(seed_content.books, "search_books", fake_books)
    monkeypatch.setattr(seed_content.locations, "search_locations", fake_locations)

    result = asyncio.run(seed_content._fetch_all_categories(items_per_category=5))

    assert set(result.keys()) == {"movies", "albums", "games", "books", "locations"}
    assert len(result["movies"]) == 1
    assert len(result["albums"]) == 1
    assert len(result["games"]) == 1
    assert len(result["books"]) == 1
    assert len(result["locations"]) == 1

    called_categories = {entry[0] for entry in calls}
    assert called_categories == {"movies", "albums", "games", "books", "locations"}