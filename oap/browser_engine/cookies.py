"""Host-only, quota-bounded cookie jar foundation for OAP Engine."""
from __future__ import annotations

from dataclasses import dataclass
from http.cookies import SimpleCookie
from urllib.parse import urlsplit

from .origin import Origin, parse_origin

MAX_COOKIES_PER_ORIGIN = 128
MAX_COOKIE_HEADER_BYTES = 8192
MAX_COOKIE_NAME_BYTES = 256
MAX_COOKIE_VALUE_BYTES = 4096


@dataclass(frozen=True)
class Cookie:
    name: str
    value: str
    origin: Origin
    path: str
    secure: bool
    http_only: bool
    same_site: str


class CookieJar:
    def __init__(self) -> None:
        self._cookies: dict[Origin, dict[tuple[str, str], Cookie]] = {}

    @staticmethod
    def _byte_len(value: str) -> int:
        return len(value.encode("utf-8"))

    def set_cookie(self, url: object, header: object) -> None:
        raw_header = str(header or "")
        if not raw_header or self._byte_len(raw_header) > MAX_COOKIE_HEADER_BYTES:
            raise ValueError("invalid_cookie_header")

        origin = parse_origin(url)
        parsed_url = urlsplit(str(url))
        parser = SimpleCookie()
        try:
            parser.load(raw_header)
        except Exception as exc:
            raise ValueError("invalid_cookie_header") from exc
        if len(parser) != 1:
            raise ValueError("exactly_one_cookie_required")

        morsel = next(iter(parser.values()))
        name = morsel.key
        value = morsel.value
        if not name or self._byte_len(name) > MAX_COOKIE_NAME_BYTES:
            raise ValueError("invalid_cookie_name")
        if self._byte_len(value) > MAX_COOKIE_VALUE_BYTES:
            raise ValueError("cookie_value_too_large")

        domain = morsel["domain"].strip().lower()
        if domain and domain.lstrip(".") != origin.host:
            raise ValueError("cross_host_cookie_domain_not_supported")

        path = morsel["path"].strip() or "/"
        if not path.startswith("/"):
            path = "/"

        secure = bool(morsel["secure"])
        http_only = bool(morsel["httponly"])
        same_site = morsel["samesite"].strip().lower() or "lax"
        if same_site not in {"strict", "lax", "none"}:
            same_site = "lax"
        if same_site == "none" and not secure:
            raise ValueError("samesite_none_requires_secure")

        bucket = self._cookies.setdefault(origin, {})
        key = (name, path)
        if key not in bucket and len(bucket) >= MAX_COOKIES_PER_ORIGIN:
            raise ValueError("cookie_origin_limit")
        bucket[key] = Cookie(
            name=name,
            value=value,
            origin=origin,
            path=path,
            secure=secure,
            http_only=http_only,
            same_site=same_site,
        )

    def cookie_header(self, url: object, *, include_http_only: bool = False) -> str:
        origin = parse_origin(url)
        parsed = urlsplit(str(url))
        request_path = parsed.path or "/"
        pairs: list[str] = []
        for cookie in self._cookies.get(origin, {}).values():
            if cookie.secure and origin.scheme != "https":
                continue
            if cookie.http_only and not include_http_only:
                continue
            if not request_path.startswith(cookie.path):
                continue
            pairs.append(f"{cookie.name}={cookie.value}")
        return "; ".join(sorted(pairs))

    def clear_origin(self, url: object) -> None:
        self._cookies.pop(parse_origin(url), None)
