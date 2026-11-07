"""Explicit, first-party seed crawler. No background jobs, links or external search.

This module performs network IO only when crawl_seed() is explicitly invoked.
All requests use validated public DNS answers and a pinned peer IP with TLS
certificate/hostname verification; no proxies or redirects are followed.
A successful robots.txt (HTTP 200) is required (conservative first milestone).
"""
from __future__ import annotations

import html
import http.client
import ipaddress
import re
import socket
import ssl
from html.parser import HTMLParser
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

from .koradaso_web_index import _safe_public_url, ingest_public_page

USER_AGENT = "KoradasoBot/0.1 (+https://onanypostcode.global/koradaso)"
MAX_ROBOTS = 128 * 1024
MAX_HTML = 512 * 1024
TIMEOUT = 5


class CrawlerRejected(ValueError):
    """An untrusted or unavailable seed was refused; no content indexed."""


def _public_addresses(host: str) -> list[str]:
    try:
        answers = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise CrawlerRejected("dns_unavailable") from exc
    addresses = list(dict.fromkeys(answer[4][0] for answer in answers))
    if not addresses or not all(ipaddress.ip_address(addr).is_global for addr in addresses):
        raise CrawlerRejected("non_public_dns_destination")
    return addresses


class _PinnedHTTPS(http.client.HTTPSConnection):
    """Connect to a vetted IP while verifying TLS against original hostname."""

    def __init__(self, host: str, address: str) -> None:
        super().__init__(host, port=443, timeout=TIMEOUT, context=ssl.create_default_context())
        self._address = address

    def connect(self) -> None:
        sock = socket.create_connection((self._address, 443), timeout=self.timeout)
        try:
            self.sock = self._context.wrap_socket(sock, server_hostname=self.host)
        except Exception:
            sock.close()
            raise


def _connect_https(host: str, addresses: list[str]) -> _PinnedHTTPS:
    first = addresses[0]
    candidates = [first]
    if len(addresses) > 1:
        first_is_ipv6 = ":" in first
        alternate = next(
            (address for address in addresses if (":" in address) != first_is_ipv6),
            addresses[1],
        )
        candidates.append(alternate)

    last_error: OSError | None = None
    for address in candidates:
        connection = _PinnedHTTPS(host, address)
        try:
            connection.connect()
        except ssl.SSLCertVerificationError as exc:
            connection.close()
            raise CrawlerRejected("https_fetch_failed") from exc
        except OSError as exc:
            connection.close()
            last_error = exc
        else:
            return connection

    raise CrawlerRejected("https_fetch_failed") from last_error


def _fetch(host: str, target: str, *, limit: int) -> tuple[int, str, bytes]:
    """Resolve once per request and retry only before sending HTTP."""
    connection = _connect_https(host, _public_addresses(host))
    try:
        connection.request(
            "GET", target,
            headers={"Host": host, "User-Agent": USER_AGENT,
                     "Accept": "text/html,text/plain;q=0.3",
                     "Accept-Encoding": "identity", "Connection": "close"},
        )
        response = connection.getresponse()
        mime = response.getheader("Content-Type", "").lower()
        content_length = response.getheader("Content-Length")
        if content_length:
            try:
                if int(content_length) > limit:
                    raise CrawlerRejected("response_too_large")
            except ValueError as exc:
                raise CrawlerRejected("invalid_content_length") from exc
        if response.status != 200:
            return response.status, mime, b""
        data = response.read(limit + 1)
        if len(data) > limit:
            raise CrawlerRejected("response_too_large")
        return response.status, mime, data
    except (OSError, ssl.SSLError, http.client.HTTPException) as exc:
        raise CrawlerRejected("https_fetch_failed") from exc
    finally:
        connection.close()


class _PublicText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title: list[str] = []
        self.body: list[str] = []
        self.description = ""
        self._skip = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip += 1
        if tag == "title":
            self._in_title = True
        if tag == "meta":
            a = dict(attrs)
            if a.get("name", "").casefold() == "description" and a.get("content"):
                self.description = a["content"]

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip = max(0, self._skip - 1)
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        if self._in_title:
            self.title.append(data)
        else:
            self.body.append(data)


def crawl_seed(url: str, db_path) -> dict[str, str]:
    """Crawl exactly one vetted HTTPS URL and index only a real public HTML page."""
    if not _safe_public_url(url):
        raise CrawlerRejected("invalid_seed_url")
    parsed = urlsplit(url)
    host = parsed.hostname or ""
    if any(c in url for c in ("\r", "\n", "\t")) or parsed.fragment:
        raise CrawlerRejected("unsafe_seed_url")
    # Validate robots from the same public hostname, never third-party redirects.
    status, mime, robots = _fetch(host, "/robots.txt", limit=MAX_ROBOTS)
    if status != 200 or "text/plain" not in mime:
        raise CrawlerRejected("robots_policy_unavailable")
    policy = RobotFileParser()
    policy.parse(robots.decode("utf-8", errors="replace").splitlines())
    target = parsed.path or "/"
    if parsed.query:
        target += "?" + parsed.query
    if not policy.can_fetch(USER_AGENT, url):
        raise CrawlerRejected("robots_disallow")
    status, mime, content = _fetch(host, target, limit=MAX_HTML)
    if status != 200 or "text/html" not in mime:
        raise CrawlerRejected("not_public_html")
    parser = _PublicText()
    parser.feed(content.decode("utf-8", errors="replace"))
    title = re.sub(r"\s+", " ", html.unescape(" ".join(parser.title))).strip()[:200]
    description = parser.description or " ".join(parser.body)
    description = re.sub(r"\s+", " ", html.unescape(description)).strip()[:1200]
    if not title:
        raise CrawlerRejected("missing_page_title")
    ingest_public_page(db_path, url=url, title=title, description=description)
    return {"url": url, "title": title, "description": description}
