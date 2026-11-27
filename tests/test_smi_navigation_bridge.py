"""Private navigation bridge regression tests; no live service required."""
import hashlib
from unittest.mock import MagicMock

import pytest

from mission_control import smi_navigation_bridge as bridge


def test_private_context():
    assert bridge.private_context(True, "127.0.0.1:5000")
    assert bridge.private_context(True, "localhost:5000")
    assert not bridge.private_context(False, "127.0.0.1:5000")
    assert not bridge.private_context(True, "localhost:5052")
    assert not bridge.private_context(True, "example.org:5000")


@pytest.mark.parametrize("path", ["../app.py", "api/admin", "http://example.org", "roads/../secret.json"])
def test_unknown_path_denied(path):
    assert bridge.response(path, b"")[0] == 404


@pytest.mark.parametrize("query", [b"q=a&q=b", b"url=http://example.org", b"q=%00", b"q=" + b"a"*1001])
def test_invalid_query_denied(query):
    assert bridge.response("api/navigation/search", query)[0] == 400


def test_fixed_loopback_no_forwarded_credentials(monkeypatch):
    connection = MagicMock()
    upstream = connection.getresponse.return_value
    upstream.status = 200
    upstream.getheader.return_value = "application/json"
    upstream.read.return_value = b'{"ready":true}'
    factory = MagicMock(return_value=connection)
    monkeypatch.setattr(bridge.http.client, "HTTPConnection", factory)
    code, mime, _ = bridge.response("api/navigation/status", b"")
    assert (code, mime) == (200, "application/json")
    factory.assert_called_once_with("127.0.0.1", 3001, timeout=12)
    connection.request.assert_called_once_with(
        "GET", "/api/navigation/status",
        headers={"Accept": "application/json", "Connection": "close"})
    connection.close.assert_called_once()


def test_no_redirect(monkeypatch):
    connection = MagicMock()
    connection.getresponse.return_value.status = 302
    monkeypatch.setattr(bridge.http.client, "HTTPConnection", MagicMock(return_value=connection))
    assert bridge.response("api/navigation/status", b"")[0] == 502
    assert connection.request.call_count == 1


def test_unavailable_engine(monkeypatch):
    connection = MagicMock()
    connection.request.side_effect = ConnectionRefusedError
    monkeypatch.setattr(bridge.http.client, "HTTPConnection", MagicMock(return_value=connection))
    assert bridge.response("api/navigation/status", b"")[0] == 503


def test_asset_integrity_and_rewrite(tmp_path, monkeypatch):
    raw = b'<link href="/navigation.css"><script src="/navigation.mjs"></script>'
    file = tmp_path / "navigation.html"
    file.write_bytes(raw)
    monkeypatch.setattr(bridge, "ASSET_DIR", tmp_path)
    monkeypatch.setattr(bridge, "ASSETS", {
        "": ("navigation.html", "text/html", hashlib.sha256(raw).hexdigest())
    })
    code, _, body = bridge.response("", b"")
    assert code == 200
    assert b'href="navigation.css"' in body
    assert b'src="navigation.mjs"' in body
    file.write_bytes(b"<script>unexpected()</script>")
    assert bridge.response("", b"")[0] == 503


def test_route_allowlist():
    assert bridge.upstream_target(
        "api/navigation/route", b"from=-0.168%2C51.403&to=-0.17%2C51.4&mode=bike"
    ).startswith("/api/navigation/route?")
    assert bridge.upstream_target("roads/-2_3.json", b"") == "/roads/-2_3.json"
    assert bridge.response("api/navigation/route", b"from=0&to=1&mode=plane")[0] == 400
