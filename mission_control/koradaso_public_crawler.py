"""Bounded first-party KORADASO public HTTPS crawler.

Manual, owner-initiated seed crawl. No automated discovery, onion access,
private subnets, external search provider, credentials, or background worker.
Network requests use pinned, publicly routable IPs after DNS validation.
"""
from __future__ import annotations

import http.client
import ipaddress
import json
import socket
import ssl
import time
from collections import deque
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

from .koradaso_web_index import _safe_public_url, ingest_public_page

USER_AGENT = "KORADASO-PublicBot/0.1 (+https://onanypostcode.global/koradaso)"
MAX_BYTES = 256 * 1024
MAX_PAGES = 5
MAX_DEPTH = 1
TIMEOUT = 5
MAX_ROBOTS_BYTES = 128 * 1024


class CrawlDenied(ValueError):
    """The target or its robots policy forbids this crawl."""


def _target(url: str) -> tuple[str, str]:
    if not _safe_public_url(url):
        raise CrawlDenied("unsafe_public_url")
    parts = urlsplit(url)
    if parts.port not in (None, 443):
        raise CrawlDenied("unsafe_port")
    if parts.fragment:
        url = urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, ""))
    return url, parts.hostname or ""


def _public_ips(host: str) -> tuple[str, ...]:
    try:
        answers = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise CrawlDenied("dns_unavailable") from exc
    ips = {item[4][0] for item in answers}
    if not ips or any(not ipaddress.ip_address(ip).is_global for ip in ips):
        raise CrawlDenied("non_public_dns_destination")
    return tuple(sorted(ips))


class _PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self, host: str, ip: str):
        super().__init__(host, port=443, timeout=TIMEOUT, context=ssl.create_default_context())
        self._validated_ip = ip

    def connect(self) -> None:
        raw = socket.create_connection((self._validated_ip, 443), self.timeout)
        try:
            self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
        except BaseException:
            raw.close()
            raise


def _fetch(url: str, *, max_bytes: int = MAX_BYTES) -> tuple[str, bytes]:
    """Resolve and pin public IP per request; never follow HTTP redirects."""
    clean, host = _target(url)
    ips = _public_ips(host)
    parts = urlsplit(clean)
    path = parts.path or "/"
    if parts.query:
        path += "?" + parts.query
    connection = _PinnedHTTPS(host, ips[0])
    try:
        connection.request(
            "GET", path,
            headers={"Host": host, "User-Agent": USER_AGENT,
                     "Accept": "text/html,text/plain;q=0.4",
                     "Connection": "close"},
        )
        response = connection.getresponse()
        if response.status != 200:
            raise CrawlDenied("http_status_not_200")
        mime = response.getheader("Content-Type", "").split(";", 1)[0].lower().strip()
        if mime not in {"text/html", "text/plain"}:
            raise CrawlDenied("unsupported_content_type")
        length = response.getheader("Content-Length")
        if length is not None and (not length.isdecimal() or int(length) > max_bytes):
            raise CrawlDenied("oversized_response")
        body = response.read(max_bytes + 1)
        if len(body) > max_bytes:
            raise CrawlDenied("oversized_response")
        return mime, body
    except (OSError, ssl.SSLError, http.client.HTTPException) as exc:
        raise CrawlDenied("network_fetch_failed") from exc
    finally:
        connection.close()


class _Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_title = False
        self.title: list[str] = []
        self.description = ""
        self.links: list[str] = []
        self.noindex = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if tag == "title":
            self.in_title = True
        if tag == "a" and a.get("href"):
            self.links.append(a["href"] or "")
        if tag == "meta":
            name = (a.get("name") or "").lower()
            value = a.get("content") or ""
            if name == "description":
                self.description = value[:1200]
            if name in {"robots", "koradaso-publicbot"} and "noindex" in value.lower():
                self.noindex = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title.append(data)


def _robots(host: str) -> RobotFileParser:
    parser = RobotFileParser()
    url = "https://" + host + "/robots.txt"
    try:
        mime, body = _fetch(url, max_bytes=MAX_ROBOTS_BYTES)
        if mime not in {"text/plain", "text/html"}:
            raise CrawlDenied("robots_invalid")
        parser.parse(body.decode("utf-8", "replace").splitlines())
    except CrawlDenied:
        # Fail closed on unavailable or ambiguous robots responses.
        raise CrawlDenied("robots_unavailable_or_denied") from None
    return parser


def crawl_public_seed(
    seed: str, database: Path, *, max_pages: int = MAX_PAGES,
    sleep_seconds: float = 1.0,
) -> dict[str, object]:
    """Crawl only one pre-approved HTTPS host, max one link-depth, no redirects.

    Requires an existing, accessible robots.txt with explicit policy.
    Does not follow cross-origin links, download binaries, or run automatically.
    """
    seed, host = _target(seed)
    max_pages = max(1, min(MAX_PAGES, int(max_pages)))
    robots = _robots(host)
    pending = deque([(seed, 0)])
    visited: set[str] = set()
    imported = 0
    denied = 0
    errors: list[str] = []
    while pending and len(visited) < max_pages:
        url, depth = pending.popleft()
        if url in visited:
            continue
        visited.add(url)
        if not robots.can_fetch(USER_AGENT, url):
            denied += 1
            continue
        try:
            mime, content = _fetch(url)
            if mime != "text/html":
                denied += 1
                continue
            parsed = _Page()
            parsed.feed(content.decode("utf-8", "replace"))
            title = " ".join(parsed.title).strip()[:200]
            if parsed.noindex or not title:
                denied += 1
                continue
            ingest_public_page(database, url=url, title=title,
                               description=parsed.description)
            imported += 1
            if depth < MAX_DEPTH:
                for href in parsed.links[:40]:
                    candidate = urljoin(url, href)
                    try:
                        candidate, next_host = _target(candidate)
                    except (CrawlDenied, ValueError):
                        continue
                    if next_host == host and candidate not in visited:
                        pending.append((candidate, depth + 1))
        except (CrawlDenied, ValueError, UnicodeError, OSError) as exc:
            errors.append(str(exc)[:80])
        if pending and sleep_seconds > 0:
            time.sleep(max(1.0, float(sleep_seconds)))
    return {"visited": len(visited), "indexed": imported, "skipped": denied,
            "errors": errors, "scope": "one_public_https_host", "auto_run": False}
