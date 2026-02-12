"""
Shared async HTTP client used by all external API services.

Provides a managed httpx.AsyncClient with timeout, retries,
and consistent error handling.
"""

from __future__ import annotations

import httpx
from typing import Any

from .config import REQUEST_TIMEOUT


async def get_client() -> httpx.AsyncClient:
    """Create a new async HTTP client with default settings."""
    return httpx.AsyncClient(
        timeout=httpx.Timeout(REQUEST_TIMEOUT),
        follow_redirects=True,
        headers={"Accept": "application/json"},
    )


async def fetch_json(
    url: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> Any:
    """
    Perform a GET request and return parsed JSON.

    Raises:
        httpx.HTTPStatusError: on 4xx / 5xx responses.
        httpx.RequestError: on network / timeout errors.
    """
    async with await get_client() as client:
        response = await client.get(url, params=params, headers=headers or {})
        response.raise_for_status()
        return response.json()


async def post_json(
    url: str,
    *,
    body: str | None = None,
    data: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
) -> Any:
    """
    Perform a POST request and return parsed JSON.

    Args:
        body: Raw text body for POST endpoints.
        data: Form-encoded body.
        headers: Extra headers merged with defaults.
        params: Query-string parameters.
    """
    async with await get_client() as client:
        kwargs: dict[str, Any] = {}
        if params:
            kwargs["params"] = params
        if headers:
            kwargs["headers"] = headers
        if body is not None:
            kwargs["content"] = body
        elif data is not None:
            kwargs["data"] = data
        response = await client.post(url, **kwargs)
        response.raise_for_status()
        return response.json()
