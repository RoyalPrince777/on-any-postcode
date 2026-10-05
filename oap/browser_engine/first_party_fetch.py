"""Bounded first-party fetch pipeline for certified OAP public routes."""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlsplit

from flask import Flask

from .cache import ResponseCache

MAX_RESPONSE_BYTES = 2 * 1024 * 1024
CERTIFIED_FETCH_PATHS = frozenset({
    "/",
    "/world",
    "/search",
    "/the-spot",
    "/the-link",
    "/arena",
    "/library",
    "/oap-map",
    "/movement",
    "/booking",
    "/music",
    "/transport",
    "/linkup",
})
ALLOWED_FETCH_METHODS = frozenset({"GET", "HEAD"})


@dataclass(frozen=True)
class FirstPartyFetchResult:
    target: str
    method: str
    status_code: int
    content_type: str
    body: bytes
    redirect_location: str | None
    from_cache: bool

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300


def canonical_first_party_target(raw_target: object) -> str:
    target = str(raw_target or "").strip()
    if not target or len(target) > 2048:
        raise ValueError("invalid_first_party_target")

    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or parsed.fragment:
        raise ValueError("first_party_target_must_be_relative")
    if parsed.path not in CERTIFIED_FETCH_PATHS:
        raise ValueError("uncertified_first_party_target")

    pairs = parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=False)
    if len(pairs) > 32:
        raise ValueError("first_party_query_field_limit")
    for key, value in pairs:
        if len(key.encode("utf-8")) > 256 or len(value.encode("utf-8")) > 4096:
            raise ValueError("first_party_query_field_too_large")

    query = urlencode(pairs, doseq=True)
    return parsed.path + (f"?{query}" if query else "")


def fetch_first_party(
    app: Flask,
    raw_target: object,
    *,
    method: object = "GET",
    cache: ResponseCache | None = None,
    cache_origin: str = "https://on-any-postcode.onrender.com",
) -> FirstPartyFetchResult:
    target = canonical_first_party_target(raw_target)
    clean_method = str(method or "GET").strip().upper()
    if clean_method not in ALLOWED_FETCH_METHODS:
        raise ValueError("unsupported_first_party_fetch_method")

    cache_url = cache_origin.rstrip("/") + target
    if clean_method == "GET" and cache is not None:
        cached = cache.get(cache_url)
        if cached is not None:
            return FirstPartyFetchResult(
                target=target,
                method=clean_method,
                status_code=200,
                content_type=cached.content_type,
                body=cached.body,
                redirect_location=None,
                from_cache=True,
            )

    with app.test_client() as client:
        response = client.open(
            target,
            method=clean_method,
            headers={
                "X-OAP-Engine-Internal": "1",
                "Accept": "text/html,application/json;q=0.8",
            },
            follow_redirects=False,
        )

    body = response.get_data()
    if len(body) > MAX_RESPONSE_BYTES:
        raise ValueError("first_party_response_too_large")

    content_type = response.headers.get("Content-Type", "")[:256]
    redirect_location = response.headers.get("Location")
    if redirect_location is not None:
        try:
            redirect_location = canonical_first_party_target(redirect_location)
        except ValueError:
            redirect_location = None

    if (
        clean_method == "GET"
        and cache is not None
        and response.status_code == 200
        and ("text/html" in content_type or "application/json" in content_type)
    ):
        cache.put(cache_url, body, content_type=content_type)

    return FirstPartyFetchResult(
        target=target,
        method=clean_method,
        status_code=response.status_code,
        content_type=content_type,
        body=body,
        redirect_location=redirect_location,
        from_cache=False,
    )
