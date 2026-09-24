"""Negative tests for the isolated, metadata-only OAP Music source fetch."""
from unittest.mock import patch

import pytest

from mission_control import music_source_fetch as fetch


class _Response:
    status = 200

    def __init__(self, body=b"<html><title>Exact track page</title></html>",
                 content_type="text/html", encoding="identity"):
        self.body = body
        self.content_type = content_type
        self.encoding = encoding

    def getheader(self, name, default=None):
        return {
            "Content-Type": self.content_type,
            "Content-Encoding": self.encoding,
            "Content-Length": str(len(self.body)),
        }.get(name, default)

    def read(self, limit):
        return self.body[:limit]


class _Connection:
    def __init__(self, host, address):
        self.host = host
        self.address = address
        self.response = _Response()
        self.requests = []
        self.closed = False

    def request(self, method, path, headers):
        self.requests.append((method, path, headers))

    def getresponse(self):
        return self.response

    def close(self):
        self.closed = True


URL = "https://freemusicarchive.org/music/artist/exact-track/"


def test_default_denies_without_any_network(monkeypatch):
    monkeypatch.setattr(fetch, "_public_addresses",
                        lambda host: pytest.fail("DNS must not run"))
    with pytest.raises(fetch.SourceFetchDenied, match="source_permission_required"):
        fetch.fetch_permitted_track_page("free_music_archive", URL)


def test_rejects_host_spoof_redirect_and_private_dns(monkeypatch):
    with pytest.raises(fetch.SourceFetchDenied, match="invalid_source_page"):
        fetch.fetch_permitted_track_page(
            "free_music_archive", "https://freemusicarchive.org.evil.test/music/x",
            source_permission=True, stop_check=lambda: False,
        )
    with patch.object(fetch.socket, "getaddrinfo", return_value=[
        (2, 1, 6, "", ("127.0.0.1", 443)),
    ]), pytest.raises(fetch.SourceFetchDenied, match="non_public_dns"):
        fetch.fetch_permitted_track_page(
            "free_music_archive", URL, source_permission=True, stop_check=lambda: False,
        )
    conn = _Connection("freemusicarchive.org", "8.8.8.8")
    conn.response.status = 302
    monkeypatch.setattr(fetch, "_public_addresses", lambda host: ("8.8.8.8",))
    monkeypatch.setattr(fetch, "_PinnedHTTPS", lambda host, address: conn)
    with pytest.raises(fetch.SourceFetchDenied, match="source_response_not_200"):
        fetch.fetch_permitted_track_page(
            "free_music_archive", URL, source_permission=True, stop_check=lambda: False,
        )
    assert conn.closed


def test_exact_html_page_is_a_non_authoritative_hash_receipt(monkeypatch):
    conn = _Connection("freemusicarchive.org", "8.8.8.8")
    monkeypatch.setattr(fetch, "_public_addresses", lambda host: ("8.8.8.8",))
    monkeypatch.setattr(fetch, "_PinnedHTTPS", lambda host, address: conn)
    result = fetch.fetch_permitted_track_page(
        "free_music_archive", URL, source_permission=True, stop_check=lambda: False,
    )
    assert result["html_title"] == "Exact track page"
    assert len(result["source_page_sha256"]) == 64
    assert result["source_page_byte_length"] == len(conn.response.body)
    assert conn.requests[0][0] == "GET"
    assert conn.requests[0][2]["Accept"] == "text/html"
    assert conn.requests[0][2]["Accept-Encoding"] == "identity"
    assert result["source_page_retrieved"] is True
    assert result["source_page_independently_checked"] is False
    assert result["licence_verified"] is False
    assert result["recording_rights_verified"] is False
    assert result["composition_rights_verified"] is False
    assert result["receipt_persisted"] is False
    assert result["audio_retrieval_performed"] is False
    assert result["playback_enabled"] is False
    assert conn.closed


@pytest.mark.parametrize("body,mime,encoding", [
    (b"x" * (fetch.MAX_PAGE_BYTES + 1), "text/html", "identity"),
    (b"mp3bytes", "audio/mpeg", "identity"),
    (b"compressed", "text/html", "gzip"),
])
def test_no_oversize_audio_or_compressed_data(monkeypatch, body, mime, encoding):
    conn = _Connection("freemusicarchive.org", "8.8.8.8")
    conn.response = _Response(body=body, content_type=mime, encoding=encoding)
    monkeypatch.setattr(fetch, "_public_addresses", lambda host: ("8.8.8.8",))
    monkeypatch.setattr(fetch, "_PinnedHTTPS", lambda host, address: conn)
    with pytest.raises(fetch.SourceFetchDenied):
        fetch.fetch_permitted_track_page(
            "free_music_archive", URL, source_permission=True, stop_check=lambda: False,
        )
    assert conn.closed


def test_stop_authority_required_before_dns(monkeypatch):
    monkeypatch.setattr(fetch, "_public_addresses",
                        lambda host: pytest.fail("DNS must not run"))
    with pytest.raises(fetch.SourceFetchDenied, match="stop_check_required"):
        fetch.fetch_permitted_track_page(
            "free_music_archive", URL, source_permission=True,
        )
    with pytest.raises(fetch.SourceFetchDenied, match="stopped"):
        fetch.fetch_permitted_track_page(
            "free_music_archive", URL, source_permission=True,
            stop_check=lambda: True,
        )
    with pytest.raises(fetch.SourceFetchDenied, match="stop_check_unavailable"):
        fetch.fetch_permitted_track_page(
            "free_music_archive", URL, source_permission=True,
            stop_check=lambda: 1 / 0,
        )


def test_stop_after_fetch_prevents_receipt_and_closes_connection(monkeypatch):
    conn = _Connection("freemusicarchive.org", "8.8.8.8")
    monkeypatch.setattr(fetch, "_public_addresses", lambda host: ("8.8.8.8",))
    monkeypatch.setattr(fetch, "_PinnedHTTPS", lambda host, address: conn)
    observations = iter((False, True))
    with pytest.raises(fetch.SourceFetchDenied, match="stopped"):
        fetch.fetch_permitted_track_page(
            "free_music_archive", URL, source_permission=True,
            stop_check=lambda: next(observations),
        )
    assert conn.closed
