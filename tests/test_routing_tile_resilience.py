from http.client import IncompleteRead

from mission_control import routing


class _TileResponse:
    def __init__(self, body: bytes):
        self._body = body
        self.headers = {"Content-Type": "application/x-protobuf"}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def geturl(self):
        return "https://routing.example/tile"

    def read(self, _limit):
        return self._body


def test_request_bytes_retries_truncated_chunked_tile(monkeypatch):
    calls = {"count": 0}

    def fake_urlopen(_request, timeout):
        assert timeout == routing.ROUTE_TIMEOUT_SECONDS
        calls["count"] += 1
        if calls["count"] == 1:
            raise IncompleteRead(b"partial", 20)
        return _TileResponse(b"complete-vector-tile")

    monkeypatch.setattr(routing.urlrequest, "urlopen", fake_urlopen)
    monkeypatch.setattr(routing.time, "sleep", lambda _seconds: None)

    body, content_type = routing._request_bytes(
        "https://routing.example/tile",
        expected_host="routing.example",
        max_bytes=1024,
    )

    assert body == b"complete-vector-tile"
    assert content_type == "application/x-protobuf"
    assert calls["count"] == 2


def test_request_bytes_fails_closed_after_repeated_truncation(monkeypatch):
    def fake_urlopen(_request, timeout):
        assert timeout == routing.ROUTE_TIMEOUT_SECONDS
        raise IncompleteRead(b"partial", 20)

    monkeypatch.setattr(routing.urlrequest, "urlopen", fake_urlopen)
    monkeypatch.setattr(routing.time, "sleep", lambda _seconds: None)

    try:
        routing._request_bytes(
            "https://routing.example/tile",
            expected_host="routing.example",
            max_bytes=1024,
        )
    except routing.RoutingUnavailable as exc:
        assert str(exc) == "routing_provider_unavailable"
    else:
        raise AssertionError("truncated road tile must fail closed")
