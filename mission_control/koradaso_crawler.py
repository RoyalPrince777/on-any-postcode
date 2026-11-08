"""Explicit, first-party seed crawler. No background jobs, links or external search.

This module performs network IO only when crawl_seed() is explicitly invoked.
All requests use validated public DNS answers and a pinned peer IP with TLS
certificate/hostname verification; no proxies or redirects are followed.
A successful robots.txt (HTTP 200) is required (conservative first milestone).
"""
from __future__ import annotations

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
                size = int(content_length)
            except ValueError as exc:
                raise CrawlerRejected("invalid_content_length") from exc
            if size < 0:
                raise CrawlerRejected("invalid_content_length")
            if size > limit:
                raise CrawlerRejected("response_too_large")
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
    _IGNORED = {"aside", "footer", "form", "header", "nav", "noscript", "script",
                "style", "svg", "template"}
    _VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
             "meta", "param", "source", "track", "wbr"}
    _BLOCK = {"article", "br", "div", "h1", "h2", "h3", "li", "main", "p", "section"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title: list[str] = []
        self.description = ""
        self._body: list[str] = []
        self._main: list[str] = []
        self._paragraphs: list[str] = []
        self._ignored: list[str] = []
        self._content: list[str] = []
        self._in_title = False
        self._in_head = False
        self._in_paragraph = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._ignored:
            if tag == self._ignored[-1]:
                self._ignored.append(tag)
            return
        attributes = dict(attrs)
        role = (attributes.get("role") or "").casefold()
        if tag not in self._VOID and (
            tag in self._IGNORED
            or role in {"banner", "complementary", "contentinfo", "navigation", "search"}
            or "hidden" in attributes
            or (attributes.get("aria-hidden") or "").casefold() == "true"
        ):
            self._ignored.append(tag)
            return
        if tag == "head":
            self._in_head = True
        elif tag == "title":
            self._in_title = True
        elif tag == "meta" and (attributes.get("name") or "").casefold() == "description":
            self.description = attributes.get("content") or ""
        if tag in {"main", "article"} or (role == "main" and tag not in self._VOID) or (
            self._content and tag == self._content[-1]
        ):
            self._content.append(tag)
        if tag == "p":
            self._in_paragraph = True
        if tag in self._BLOCK:
            self.handle_data(" ")

    def handle_endtag(self, tag: str) -> None:
        if self._ignored:
            if tag == self._ignored[-1]:
                self._ignored.pop()
            return
        if tag in self._BLOCK:
            self.handle_data(" ")
        if self._content and tag == self._content[-1]:
            self._content.pop()
        if tag == "p":
            self._in_paragraph = False
        elif tag == "title":
            self._in_title = False
        elif tag == "head":
            self._in_head = False

    def handle_data(self, data: str) -> None:
        if self._ignored:
            return
        if self._in_title:
            self.title.append(data)
        elif not self._in_head:
            self._body.append(data)
            if self._content:
                self._main.append(data)
            if self._in_paragraph:
                self._paragraphs.append(data)

    def page_description(self) -> str:
        if self.description.strip():
            return re.sub(r"\s+", " ", self.description).strip()[:1200]
        for chunks in (self._main, self._paragraphs, self._body):
            text = re.sub(r"\s+", " ", "".join(chunks)).strip()
            if text:
                return text[:1200]
        return ""


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
    title = re.sub(r"\s+", " ", "".join(parser.title)).strip()[:200]
    description = parser.page_description()
    if not title:
        raise CrawlerRejected("missing_page_title")
    ingest_public_page(db_path, url=url, title=title, description=description)
    return {"url": url, "title": title, "description": description}
