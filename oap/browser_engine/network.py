"""Bounded request policy for future OAP Engine networking."""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit

from .origin import parse_origin, same_origin

ALLOWED_METHODS = frozenset({"GET", "HEAD", "POST"})
MAX_REQUEST_BODY_BYTES = 1024 * 1024


@dataclass(frozen=True)
class NetworkRequest:
    url: str
    method: str
    body: bytes
    include_credentials: bool


def build_request(
    url: object,
    *,
    method: object = "GET",
    body: bytes = b"",
    initiator_url: object | None = None,
) -> NetworkRequest:
    raw_url = str(url or "").strip()
    parse_origin(raw_url)
    parsed = urlsplit(raw_url)
    if parsed.username or parsed.password:
        raise ValueError("url_credentials_not_allowed")

    clean_method = str(method or "GET").strip().upper()
    if clean_method not in ALLOWED_METHODS:
        raise ValueError("unsupported_request_method")

    payload = bytes(body)
    if len(payload) > MAX_REQUEST_BODY_BYTES:
        raise ValueError("request_body_too_large")
    if clean_method in {"GET", "HEAD"} and payload:
        raise ValueError("request_body_not_allowed")

    include_credentials = bool(
        initiator_url is not None and same_origin(initiator_url, raw_url)
    )
    return NetworkRequest(
        url=raw_url,
        method=clean_method,
        body=payload,
        include_credentials=include_credentials,
    )
