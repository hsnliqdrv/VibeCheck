"""
Books service — powered by the Open Library API.

API docs: https://openlibrary.org/developers/api
Completely free, no API key required.

Returns data shaped to the VibeCheck Book schema:
    id, title, author, cover, totalPages, url
"""

from __future__ import annotations

from typing import Any

from .base import fetch_json
from .config import OPENLIBRARY_BASE_URL


def _normalize_book_from_search(raw: dict[str, Any]) -> dict[str, Any]:
    """Map an Open Library search result to the VibeCheck Book schema."""
    key = raw.get("key", "")  # e.g. "/works/OL45883W"
    ol_id = key.replace("/works/", "")
    cover_id = raw.get("cover_i")

    return {
        "id": ol_id,
        "title": raw.get("title", ""),
        "author": ", ".join(raw.get("author_name", [])) or "Unknown",
        "cover": (
            f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
            if cover_id
            else None
        ),
        "totalPages": raw.get("number_of_pages_median"),
        "url": f"https://openlibrary.org{key}" if key else None,
    }


async def _resolve_author_name(author_key: str) -> str:
    """Fetch author name from Open Library by author key (e.g. '/authors/OL79034A')."""
    try:
        raw = await fetch_json(f"{OPENLIBRARY_BASE_URL}{author_key}.json")
        return raw.get("name", "Unknown")
    except Exception:
        return "Unknown"


async def _normalize_book_detail(raw: dict[str, Any], ol_id: str) -> dict[str, Any]:
    """Map an Open Library works response to the VibeCheck Book schema."""
    # Authors in the works endpoint are references — resolve names via API
    authors = raw.get("authors", [])
    author_names: list[str] = []
    for a in authors:
        author_obj = a.get("author", a)
        if isinstance(author_obj, dict):
            name = author_obj.get("name")
            if not name:
                key = author_obj.get("key", "")
                if key:
                    name = await _resolve_author_name(key)
                else:
                    name = "Unknown"
            author_names.append(name)

    covers = raw.get("covers", [])
    cover_url = (
        f"https://covers.openlibrary.org/b/id/{covers[0]}-L.jpg" if covers else None
    )

    # Description can be a string or {"type": ..., "value": ...}
    description = raw.get("description", "")
    if isinstance(description, dict):
        description = description.get("value", "")

    return {
        "id": ol_id,
        "title": raw.get("title", ""),
        "author": ", ".join(author_names) or "Unknown",
        "cover": cover_url,
        "totalPages": None,  # works endpoint doesn't have page counts
        "url": f"https://openlibrary.org/works/{ol_id}",
    }


# ── Public API ────────────────────────────────────────────────────


async def search_books(
    query: str,
    *,
    author: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict[str, Any]:
    """
    Search books by title or author.

    Returns:
        {
            "data": [Book, ...],
            "total": int,
            "limit": int,
            "offset": int,
        }
    """
    params: dict[str, Any] = {
        "q": query,
        "limit": limit,
        "offset": offset,
        "fields": "key,title,author_name,cover_i,number_of_pages_median",
    }
    if author:
        params["author"] = author

    raw = await fetch_json(f"{OPENLIBRARY_BASE_URL}/search.json", params=params)

    books = [_normalize_book_from_search(b) for b in raw.get("docs", [])]

    return {
        "data": books,
        "total": raw.get("numFound", len(books)),
        "limit": limit,
        "offset": offset,
    }


async def get_book_by_id(book_id: str) -> dict[str, Any] | None:
    """
    Get detailed book info by Open Library work ID (e.g. 'OL45883W').

    Returns a Book dict or None if not found.
    """
    try:
        raw = await fetch_json(f"{OPENLIBRARY_BASE_URL}/works/{book_id}.json")
    except Exception:
        return None

    if raw.get("error"):
        return None

    return await _normalize_book_detail(raw, book_id)
