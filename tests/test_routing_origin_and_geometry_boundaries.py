"""Configuration and response trust boundaries; these are not live-host proof."""
import copy
import json

import pytest

from scripts import routing_live_green_gate as gate


def test_missing_origin_fails_before_any_network_request(monkeypatch, capsys):
    monkeypatch.delenv("OAP_ROUTING_BASE_URL", raising=False)
    def unexpected(*args, **kwargs):
        raise AssertionError("Missing origin must not issue a request")
    monkeypatch.setattr(gate._OPENER, "open", unexpected)
    with pytest.raises(SystemExit, match="OAP_ROUTING_BASE_URL is required"):
        gate.main()
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["ready"] is False
    assert receipt["failure_type"] == "invalid_or_missing_origin"
    assert receipt["dispatch_performed"] is False
    assert receipt["payment_performed"] is False


def _payload():
    return {"code": "Ok", "routes": [{
        "distance": 14000.0, "duration": 2400.0,
        "geometry": {"type": "LineString", "coordinates": [[-0.1687, 51.4036], [-0.0877, 51.5079]]},
    }]}


def test_valid_route_metrics_are_accepted():
    assert gate._route_metrics(_payload(), 200) == (14000.0, 2400.0)
    assert gate._route_metrics(_payload(), 503) is None


@pytest.mark.parametrize("field,value", [
    ("distance", 0), ("distance", -1), ("distance", True),
    ("distance", "14000"), ("distance", float("nan")),
    ("duration", float("inf")), ("duration", None),
])
def test_invalid_metrics_do_not_prove_geometry(field, value):
    payload = _payload()
    payload["routes"][0][field] = value
    assert gate._route_metrics(payload, 200) is None


@pytest.mark.parametrize("coordinates", [
    None, [], [[0, 0]], [None, None],
    [[0, 0], [181, 51]], [[0, 0], [0, 91]],
    [[0, 0], [True, 51]], [[0, 0], [float("nan"), 51]],
    [[0, 0], ["0.1", 51]], [[0, 0], [0, 0]],
    [[0, 0], [0.1, 51, 4]],
])
def test_invalid_coordinates_fail_warmup_and_capacity(monkeypatch, coordinates):
    payload = copy.deepcopy(_payload())
    payload["routes"][0]["geometry"]["coordinates"] = coordinates
    class Response:
        status = 200
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self):
            return json.dumps(payload).encode()
    monkeypatch.setenv("OAP_ROUTING_BASE_URL", "https://routing.oap.invalid")
    monkeypatch.setattr(gate._OPENER, "open", lambda *args, **kwargs: Response())
    monkeypatch.setattr(gate, "WARMUP_ATTEMPTS", 1)
    assert gate.wait_until_ready()["ready"] is False
    result = gate.run_one(0)
    assert result["ok"] is False
    assert result["distance_m"] == 0
    assert result["duration_s"] == 0


@pytest.mark.parametrize("payload", [None, [], {}, {"code": "Ok", "routes": [None]}, {"code": "Ok", "routes": {}}])
def test_malformed_route_structure_is_rejected(payload):
    assert gate._route_metrics(payload, 200) is None
