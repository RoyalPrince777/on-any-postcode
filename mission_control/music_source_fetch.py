"""Metadata-only, permission-gated source-page fetch for private OAP Music review.

Not connected to a route, catalogue, audio store or rights authority. Source
permission must be decided independently by server policy, never user JSON.
"""
from __future__ import annotations

import hashlib
import http.client
import ipaddress
import socket
import ssl
from collections.abc import Callable
from html.parser import HTMLParser
from urllib.parse import urlsplit

from .open_music_intake import _source_page

MAX_PAGE_BYTES = 65_536
MAX_METADATA_CHARS = 300


class SourceFetchDenied(ValueError):
    """Page is outside the bounded metadata-only source policy."""


class _PinnedHTTPS(http.client.HTTPSConnection):
    """TLS verifies the original hostname while TCP uses the validated IP."""

    def __init__(self, host: str, address: str) -> None:
        super().__init__(host, port=443, timeout=4, context=ssl.create_default_context())
        self._address = address

    def connect(self) -> None:
        raw = socket.create_connection((self._address, 443), self.timeout)
        try:
            self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
        except Exception:
            raw.close()
            raise


def _public_addresses(host: str) -> tuple[str, ...]:
    try:
        answers = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise SourceFetchDenied("dns_unavailable") from exc
    addresses = tuple(sorted({entry[4][0] for entry in answers}))
    if not addresses or any(not ipaddress.ip_address(a).is_global for a in addresses):
        raise SourceFetchDenied("non_public_dns")
    return addresses


class _PageTitle(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_title = False
        self.words: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "title":
            self.in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title and sum(map(len, self.words)) < MAX_METADATA_CHARS:
            self.words.append(data[:MAX_METADATA_CHARS])


def fetch_permitted_track_page(
    source_kind: str, page_url: str, *, source_permission: bool = False,
    stop_check: Callable[[], bool] | None = None,
) -> dict[str, object]:
    """Fetch one explicitly permitted HTML page, not media or a licence verdict.

    An explicit server-side source_permission is necessary but not sufficient:
    the source URL, all DNS answers, peer IP, TLS name, response status, content
    type, and byte limit must also satisfy policy. Redirects are refused.
    No network call happens on the default/denied path.
    """
    if source_permission is not True:
        raise SourceFetchDenied("source_permission_required")
    if stop_check is None or not callable(stop_check):
        raise SourceFetchDenied("stop_check_required")
    try:
        if stop_check():
            raise SourceFetchDenied("stopped")
    except SourceFetchDenied:
        raise
    except Exception as exc:
        raise SourceFetchDenied("stop_check_unavailable") from exc
    url = _source_page(source_kind, page_url)
    if url is None:
        raise SourceFetchDenied("invalid_source_page")
    parts = urlsplit(url)
    addresses = _public_addresses(parts.hostname or "")
    conn = _PinnedHTTPS(parts.hostname or "", addresses[0])
    try:
        path = parts.path  # URL policy rejects query, fragment, port and credentials.
        conn.request("GET", path, headers={
            "Accept": "text/html",
            "Accept-Encoding": "identity",
            "User-Agent": "OAP-Music-Private-Evidence/1.0",
            "Connection": "close",
        })
        response = conn.getresponse()
        if response.status != 200:
            raise SourceFetchDenied("source_response_not_200")
        mime = response.getheader("Content-Type", "").split(";", 1)[0].strip().lower()
        if mime not in ("text/html", "application/xhtml+xml"):
            raise SourceFetchDenied("non_html_source")
        if response.getheader("Content-Encoding", "identity").lower() != "identity":
            raise SourceFetchDenied("encoded_source")
        size = response.getheader("Content-Length")
        if size is not None and (not size.isdecimal() or int(size) > MAX_PAGE_BYTES):
            raise SourceFetchDenied("oversize_source")
        body = response.read(MAX_PAGE_BYTES + 1)
        if len(body) > MAX_PAGE_BYTES:
            raise SourceFetchDenied("oversize_source")
    except (OSError, ssl.SSLError, http.client.HTTPException) as exc:
        raise SourceFetchDenied("source_fetch_failed") from exc
    finally:
        conn.close()
    try:
        if stop_check():
            raise SourceFetchDenied("stopped")
    except SourceFetchDenied:
        raise
    except Exception as exc:
        raise SourceFetchDenied("stop_check_unavailable") from exc
    parser = _PageTitle()
    parser.feed(body.decode("utf-8", errors="replace"))
    return {
        "source_kind": source_kind,
        "source_page_url": url,
        "html_title": " ".join(" ".join(parser.words).split())[:MAX_METADATA_CHARS],
        "source_page_sha256": hashlib.sha256(body).hexdigest(),
        "source_page_byte_length": len(body),
        "source_page_retrieved": True,
        "source_page_independently_checked": False,
        "licence_verified": False,
        "recording_rights_verified": False,
        "composition_rights_verified": False,
        "source_asset_integrity_verified": False,
        "receipt_persisted": False,
        "audio_retrieval_performed": False,
        "playback_enabled": False,
        "public_catalogue_enabled": False,
        "human_authority_final": True,
    }
