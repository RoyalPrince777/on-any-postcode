"""OAP Engine origin and safe URL primitives."""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit


@dataclass(frozen=True, order=True)
class Origin:
    scheme: str
    host: str
    port: int

    def serialize(self) -> str:
        default = 443 if self.scheme == "https" else 80
        suffix = "" if self.port == default else f":{self.port}"
        return f"{self.scheme}://{self.host}{suffix}"


def parse_origin(raw_url: object) -> Origin:
    parsed = urlsplit(str(raw_url or "").strip())
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"}:
        raise ValueError("unsupported_origin_scheme")
    if not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("invalid_origin")
    try:
        explicit_port = parsed.port
    except ValueError as exc:
        raise ValueError("invalid_origin_port") from exc
    port = explicit_port or (443 if scheme == "https" else 80)
    if not 1 <= port <= 65535:
        raise ValueError("invalid_origin_port")
    return Origin(scheme=scheme, host=parsed.hostname.lower(), port=port)


def same_origin(left: object, right: object) -> bool:
    try:
        return parse_origin(left) == parse_origin(right)
    except ValueError:
        return False


def resolve_http_url(base_url: object, reference: object) -> str | None:
    """Resolve one reference and fail closed outside HTTP(S)."""

    try:
        base = str(base_url or "").strip()
        parse_origin(base)
    except ValueError:
        return None

    absolute = urljoin(base, str(reference or "").strip())
    try:
        parse_origin(absolute)
    except ValueError:
        return None
    return absolute
