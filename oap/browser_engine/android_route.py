"""Bounded first-party routing for Android OAP Engine documents."""
from __future__ import annotations

from urllib.parse import parse_qs, urlencode, urljoin, urlsplit

from flask import Flask

from .cache import ResponseCache
from .engine import render_html
from .first_party_fetch import fetch_first_party

SUPPORTED_PATHS = frozenset({"/", "/world", "/search"})
MAX_QUERY_LENGTH = 120
_DOCUMENT_CACHE = ResponseCache()


def canonical_supported_target(raw_target: object) -> str | None:
    target = str(raw_target or "").strip()
    if not target or len(target) > 512:
        return None

    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or parsed.fragment:
        return None
    if parsed.path not in SUPPORTED_PATHS:
        return None

    if parsed.path != "/search":
        if parsed.query:
            return None
        return parsed.path

    query = parse_qs(parsed.query, keep_blank_values=True)
    if set(query) - {"q"}:
        return None
    values = query.get("q", [""])
    if len(values) != 1:
        return None
    search = values[0].strip()
    if len(search) > MAX_QUERY_LENGTH:
        return None
    return "/search" + (("?" + urlencode({"q": search})) if search else "")


def _normalize_links(document: dict[str, object], base_url: str) -> None:
    items = document.get("items")
    if not isinstance(items, list):
        return
    for item in items:
        if not isinstance(item, dict):
            continue
        href = item.get("href")
        if not href:
            continue
        absolute = urljoin(base_url, str(href))
        parsed = urlsplit(absolute)
        if parsed.scheme not in {"http", "https"}:
            item["href"] = None
            item["kind"] = "text"
            continue
        item["href"] = absolute


def render_supported_target(
    app: Flask,
    raw_target: object,
    *,
    viewport_width: int,
    base_url: str,
) -> dict[str, object] | None:
    """Render one allow-listed public OAP page through the canonical OAP Engine."""

    target = canonical_supported_target(raw_target)
    if target is None:
        return None
    if viewport_width < 160 or viewport_width > 2048:
        raise ValueError("viewport_width must be between 160 and 2048")

    response = fetch_first_party(
        app,
        target,
        method="GET",
        cache=_DOCUMENT_CACHE,
        cache_origin=base_url.rstrip("/"),
    )
    if response.status_code != 200:
        return None
    if "text/html" not in response.content_type:
        return None

    document = render_html(
        response.body.decode("utf-8", errors="replace"),
        viewport_width=viewport_width,
        base_url=urljoin(base_url, target),
    ).to_dict()
    _normalize_links(document, base_url)
    document["source_path"] = target
    document["routing"] = "OAP_ENGINE_NATIVE"
    return document
