from __future__ import annotations

import json
import socket
from pathlib import Path
from urllib import error

import pytest

from scripts import routing_live_green_gate as gate


@pytest.fixture(autouse=True)
def mock_only_valid_oap_owned_origin(monkeypatch):
    """A fictitious test URL, never an assertion of a deployed OAP server."""
    monkeypatch.setenv("OAP_OSRM_BASE_URL", "https://routes.onanypostcode.com")
    monkeypatch.setenv("OAP_OSRM_ALLOWED_HOSTS", "routes.onanypostcode.com")
    monkeypatch.setenv("OAP_ROUTING_OWNED_HOSTS", "routes.onanypostcode.com")


@pytest.mark.parametrize(
    ("origin", "allowed", "owned", "reason"),
    [
        ("", "routes.onanypostcode.com", "routes.onanypostcode.com", "routing_origin_not_configured"),
        ("http://routes.onanypostcode.com", "routes.onanypostcode.com", "routes.onanypostcode.com", "routing_origin_rejected"),
        ("https://route-demo.example.org", "route-demo.example.org", "", "routing_origin_not_allowlisted_and_owned"),
        ("https://route-demo.example.org", "", "route-demo.example.org", "routing_origin_not_allowlisted_and_owned"),
        ("https://oap-routing.onrender.com", "oap-routing.onrender.com", "oap-routing.onrender.com", "routing_origin_rejected"),
        ("https://127.0.0.1", "127.0.0.1", "127.0.0.1", "routing_origin_rejected"),
        ("https://localhost", "localhost", "localhost", "routing_origin_rejected"),
        ("https://user:password@routes.onanypostcode.com", "routes.onanypostcode.com", "routes.onanypostcode.com", "routing_origin_rejected"),
        ("https://routes.onanypostcode.com:8443", "routes.onanypostcode.com", "routes.onanypostcode.com", "routing_origin_rejected"),
        ("https://routes.onanypostcode.com/route/v1", "routes.onanypostcode.com", "routes.onanypostcode.com", "routing_origin_rejected"),
        ("https://routes.onanypostcode.com?q=1", "routes.onanypostcode.com", "routes.onanypostcode.com", "routing_origin_rejected"),
    ],
)
def test_only_explicit_oap_owned_https_origin_accepted(
    monkeypatch, origin, allowed, owned, reason,
):
    monkeypatch.setenv("OAP_OSRM_BASE_URL", origin)
    monkeypatch.setenv("OAP_OSRM_ALLOWED_HOSTS", allowed)
    monkeypatch.setenv("OAP_ROUTING_OWNED_HOSTS", owned)
    with pytest.raises(gate.RoutingOriginRejected, match=reason):
        gate._configured_base()


def test_tested_host_uses_same_owned_endpoint_config_as_movement():
    assert gate._configured_base() == "https://routes.onanypostcode.com"
    assert gate._route_url(0).startswith(
        "https://routes.onanypostcode.com/route/v1/driving/"
    )


def test_missing_owned_route_host_fails_before_any_network_request(monkeypatch, capsys):
    monkeypatch.delenv("OAP_OSRM_BASE_URL")
    monkeypatch.setattr(
        gate, "_open_owned_json",
        lambda *_a, **_k: (_ for _ in ()).throw(
            AssertionError("missing host must cause zero requests")
        ),
    )
    with pytest.raises(SystemExit, match="not configured or approved"):
        gate.main()
    receipts = [
        json.loads(item) for item in capsys.readouterr().out.splitlines() if item
    ]
    assert len(receipts) == 1
    assert receipts[0]["attempts"] == 0
    assert receipts[0]["failure_reason"] == "routing_origin_not_configured"
    assert receipts[0]["dispatch_performed"] is False
    assert receipts[0]["ready"] is False


@pytest.mark.parametrize(
    ("failure", "expected_type"),
    [
        (TimeoutError("read timed out"), "timeout"),
        (error.URLError("unreachable"), "request_or_response_error"),
    ],
)
def test_failed_routing_request_returns_bounded_failure(monkeypatch, failure, expected_type):
    def fail_request(*args, **kwargs):
        raise failure

    monkeypatch.setattr(gate, "_open_owned_json", fail_request)
    result = gate.run_one(0)
    assert result["ok"] is False
    assert result["failure_type"] == expected_type
    assert result["route_id"] == "mitcham_london_bridge"
    assert result["distance_m"] == 0.0
    assert result["duration_s"] == 0.0


def test_non_object_json_is_bounded_failure(monkeypatch):
    def invalid_payload(*_args, **_kwargs):
        raise ValueError("routing_response_not_object")

    monkeypatch.setattr(gate, "_open_owned_json", invalid_payload)
    result = gate.run_one(0)
    assert result["ok"] is False
    assert result["failure_type"] == "request_or_response_error"
    assert result["distance_m"] == 0.0
    assert result["duration_s"] == 0.0


class FakeRouteResponse:
    status = 200

    def __init__(self, url, data):
        self.url = url
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def geturl(self):
        return self.url

    def read(self, size):
        return self.data[:size]


def test_redirect_is_blocked_before_following(monkeypatch):
    req = gate.request.Request(gate._route_url(0))
    with pytest.raises(gate.RoutingOriginRejected, match="routing_redirect_rejected"):
        gate._RejectRedirects().redirect_request(
            req, None, 302, "Redirect", {}, "https://example.org/route"
        )


def test_cross_host_response_cannot_pass(monkeypatch):
    monkeypatch.setattr(
        gate._OPENER,
        "open",
        lambda req, timeout: FakeRouteResponse(
            "https://unowned.example.org/route/v1/driving/anything",
            b'{"code":"Ok","routes":[]}',
        ),
    )
    with pytest.raises(gate.RoutingOriginRejected, match="routing_redirect_rejected"):
        gate._open_owned_json(gate.request.Request(gate._route_url(0)), 3)


@pytest.mark.parametrize(
    "redirected_url",
    [
        "http://routes.onanypostcode.com/route/v1/driving/anything",
        "https://unowned.example.org/route/v1/driving/anything",
    ],
)
def test_redirect_response_rejected_even_if_payload_seems_valid(monkeypatch, redirected_url):
    """Fail closed on scheme downgrade or host change."""
    monkeypatch.setattr(
        gate._OPENER, "open",
        lambda req, timeout: FakeRouteResponse(
            redirected_url,
            b'{"code":"Ok","routes":[{"distance":100,"duration":20}]}',
        ),
    )
    with pytest.raises(gate.RoutingOriginRejected, match="routing_redirect_rejected"):
        gate._open_owned_json(gate.request.Request(gate._route_url(0)), 3)


def test_oversized_json_cannot_pass(monkeypatch):
    monkeypatch.setattr(
        gate._OPENER,
        "open",
        lambda req, timeout: FakeRouteResponse(
            gate._route_url(0), b"x" * (gate.MAX_RESPONSE_BYTES + 1)
        ),
    )
    with pytest.raises(ValueError, match="routing_response_too_large"):
        gate._open_owned_json(gate.request.Request(gate._route_url(0)), 3)


def test_valid_same_host_json_response_is_bounded(monkeypatch):
    monkeypatch.setattr(
        gate._OPENER,
        "open",
        lambda req, timeout: FakeRouteResponse(
            gate._route_url(0),
            b'{"code":"Ok","routes":[]}',
        ),
    )
    status, payload = gate._open_owned_json(
        gate.request.Request(gate._route_url(0)), 3
    )
    assert status == 200
    assert payload["code"] == "Ok"


def test_probe_prints_failure_receipt_before_failing(monkeypatch, capsys):
    monkeypatch.setattr(gate, "wait_until_ready", lambda: {"ready": True, "attempts": 1, "elapsed_s": 0.0})
    monkeypatch.setattr(gate, "TOTAL_REQUESTS", 2)
    monkeypatch.setattr(gate, "WORKERS", 1)
    samples = (
        {"route_id": "a", "ok": True, "elapsed_s": 0.2},
        {"route_id": "b", "ok": False, "elapsed_s": 10.0, "failure_type": "timeout"},
    )
    monkeypatch.setattr(gate, "run_one", lambda index: samples[index])

    with pytest.raises(SystemExit, match="live routing probe had failed requests"):
        gate.main()
    receipts = [json.loads(line) for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert receipts[0]["event"] == "oap_routing_bounded_external_warmup"
    receipt = receipts[-1]
    assert receipt["event"] == "oap_routing_bounded_external_probe"
    assert receipt["requests"] == 2
    assert receipt["successes"] == 1
    assert receipt["failures"] == 1
    assert [r["route_id"] for r in receipt["route_results"]] == ["a", "b"]
    assert [r["ok"] for r in receipt["route_results"]] == [True, False]
    assert receipt["route_results"][1]["elapsed_ms"] == 10000.0
    assert all("geometry" not in r and "url" not in r for r in receipt["route_results"])
    assert receipt["timeouts"] == 1
    assert receipt["geometry_proven"] is False
    assert receipt["bounded_capacity_proven"] is False
    assert receipt["dispatch_performed"] is False
    assert receipt["payment_performed"] is False
    assert receipt["tracking_performed"] is False


def test_probe_preserves_p95_limit(monkeypatch, capsys):
    monkeypatch.setattr(gate, "wait_until_ready", lambda: {"ready": True, "attempts": 1, "elapsed_s": 0.0})
    monkeypatch.setattr(gate, "TOTAL_REQUESTS", 2)
    monkeypatch.setattr(gate, "WORKERS", 1)
    monkeypatch.setattr(
        gate,
        "run_one",
        lambda index: {"route_id": str(index), "ok": True, "elapsed_s": 7.0},
    )
    with pytest.raises(SystemExit, match="p95 exceeded 6.0s"):
        gate.main()
    receipts = [json.loads(line) for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert receipts[0]["event"] == "oap_routing_bounded_external_warmup"
    receipt = receipts[-1]
    assert receipt["event"] == "oap_routing_bounded_external_probe"
    assert receipt["successes"] == 2
    assert receipt["failures"] == 0
    assert receipt["bounded_capacity_proven"] is False


@pytest.mark.parametrize(
    ("exception", "reason"),
    [
        (error.HTTPError("https://example.invalid/route", 503, "unavailable", None, None), "http_503"),
        (error.URLError(socket.gaierror(-3, "lookup failed")), "dns_resolution_failed"),
        (error.URLError(ConnectionRefusedError("refused")), "connection_refused"),
        (error.URLError(TimeoutError("network timed out")), "timeout"),
    ],
)
def test_live_warmup_carries_sanitized_failure_reason(monkeypatch, exception, reason):
    monkeypatch.setattr(gate, "WARMUP_ATTEMPTS", 1)

    def reject(*_args, **_kwargs):
        raise exception

    monkeypatch.setattr(gate, "_open_owned_json", reject)
    receipt = gate.wait_until_ready()
    assert receipt["ready"] is False
    assert receipt["attempts"] == 1
    assert receipt["failure_reason"] == reason
    assert receipt["failure_type"] == (
        "timeout" if reason == "timeout" else "request_or_response_error"
    )
    assert "https://" not in json.dumps(receipt)
    assert "lookup failed" not in json.dumps(receipt)


def test_unready_live_routing_emits_reason_and_never_runs_capacity_probe(monkeypatch, capsys):
    monkeypatch.setattr(
        gate, "wait_until_ready",
        lambda: {
            "ready": False,
            "attempts": 6,
            "elapsed_s": 10.0,
            "failure_type": "request_or_response_error",
            "failure_reason": "http_503",
        },
    )

    def must_not_run(_index):
        raise AssertionError("Not allowed: pretend live routing when warmup failed")

    monkeypatch.setattr(gate, "run_one", must_not_run)
    with pytest.raises(SystemExit, match="live routing warmup did not become ready"):
        gate.main()
    receipts = [
        json.loads(line) for line in capsys.readouterr().out.splitlines() if line.strip()
    ]
    assert len(receipts) == 1
    assert receipts[0]["event"] == "oap_routing_bounded_external_warmup"
    assert receipts[0]["failure_reason"] == "http_503"
    assert receipts[0]["ready"] is False
    assert receipts[0]["dispatch_performed"] is False


def test_capacity_failure_includes_no_secret_url_in_reason(monkeypatch):
    error_response = error.HTTPError(
        "https://oap-routing.onrender.com/route/v1/driving/coordinates",
        502, "Gateway unavailable", None, None,
    )
    monkeypatch.setattr(
        gate, "_open_owned_json",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(error_response),
    )
    result = gate.run_one(0)
    assert result["ok"] is False
    assert result["failure_reason"] == "http_502"
    assert result["failure_type"] == "request_or_response_error"
    assert "onrender.com" not in json.dumps(result)



def test_live_green_gate_warms_before_capacity_probe():
    source = Path("scripts/routing_live_green_gate.py").read_text(encoding="utf-8")

    assert "def wait_until_ready()" in source
    assert '"event": "oap_routing_bounded_external_warmup"' in source
    assert 'if not warmup.get("ready")' in source
    assert "TOTAL_REQUESTS = 20" in source
    assert "WORKERS = 4" in source
    assert "P95_LIMIT_SECONDS = 6.0" in source

def test_twenty_distinct_real_route_candidates_not_repeated_two_pairs():
    assert gate.TOTAL_REQUESTS == 20
    assert len(gate.ROUTES) == 20
    assert len({(r[0], r[1], r[2], r[3]) for r in gate.ROUTES}) == 20
    assert len({r[4] for r in gate.ROUTES}) == 20
    assert all(-0.6 < r[0] < 0.4 and 51.2 < r[1] < 51.8
               and -0.6 < r[2] < 0.4 and 51.2 < r[3] < 51.8
               for r in gate.ROUTES)
    for i, route in enumerate(gate.ROUTES):
        assert gate._route_url(i).startswith(gate._configured_base() + "/route/v1/driving/")
        assert gate._route_url(i).count(";") == 1
        assert route[4] not in [other[4] for other in gate.ROUTES[i + 1:]]

