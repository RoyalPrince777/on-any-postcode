"""World Link: conservative URL-only sharing validation, without fetching content.

This module does not establish copyright ownership or embedding permission.
"""
from __future__ import annotations

import ipaddress
from urllib.parse import urlsplit, urlunsplit

MAX_URL_LENGTH = 2048


def validate_world_link(value: object) -> dict[str, str]:
    """Return a safe external navigation reference; never fetch or embed it."""
    if not isinstance(value, str) or not value or len(value) > MAX_URL_LENGTH:
        raise ValueError("invalid_world_link")
    if value != value.strip() or any(ord(char) < 33 or ord(char) == 127 for char in value):
        raise ValueError("invalid_world_link")
    try:
        parsed = urlsplit(value)
        host = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise ValueError("invalid_world_link") from exc
    if parsed.scheme != "https" or not host or parsed.username or parsed.password:
        raise ValueError("invalid_world_link")
    if port is not None and port != 443:
        raise ValueError("invalid_world_link")
    if host == "localhost" or host.endswith(".localhost") or host.endswith(".local"):
        raise ValueError("invalid_world_link")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        if "." not in host or any(not part for part in host.split(".")):
            raise ValueError("invalid_world_link") from None
    else:
        raise ValueError("invalid_world_link")
    if parsed.fragment:
        raise ValueError("invalid_world_link")
    return {
        "url": urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, "")),
        "source_host": host.lower(),
        "sharing_mode": "external_link_only",
        "embed_authorised": "unverified",
        "republication_authorised": "unverified",
    }
