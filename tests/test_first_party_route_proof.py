from __future__ import annotations

import pytest

from mission_control import first_party_route_proof as route_proof


def _payload():
    return {
        "code": "Ok",
        "routes": [
            {
                "distance": 13200.0,
                "duration": 2520.0,
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [-0.168, 51.403],
                        [-0.154, 51.417],
                        [-0.118, 51.505],
                    ],
                },
            }
        ],
    }


def test_first_party_route_proof_requires_oap_owned_engine(monkeypatch):
    monkeypatch.setattr(route_proof.routing, "provider_ownership", lambda: "external_candidate")
    with pytest.raises(
        route_proof.RouteProofUnavailable,
        match="oap_owned_route_engine_required",
    ):
        route_proof.prove_route_geometry(
            pickup_latitude=51.403,
            pickup_longitude=-0.168,
            destination_latitude=51.505,
            destination_longitude=-0.118,
        )


def test_first_party_route_proof_returns_source_backed_geometry(monkeypatch):
    monkeypatch.setattr(route_proof.routing, "provider_ownership", lambda: "oap_owned")
    monkeypatch.setattr(route_proof.routing, "production_gate_approved", lambda: True)
    monkeypatch.setattr(
        route_proof.routing,
        "_base_url",
        lambda: "https://routes.oap.invalid",
    )
    captured = {}

    def request_json(url, *, expected_host):
        captured["url"] = url
        captured["host"] = expected_host
        return _payload()

    monkeypatch.setattr(route_proof.routing, "_request_json", request_json)
    monkeypatch.setattr(route_proof.routing, "_mark_success", lambda: None)

    result = route_proof.prove_route_geometry(
        pickup_latitude=51.403,
        pickup_longitude=-0.168,
        destination_latitude=51.505,
        destination_longitude=-0.118,
        profile="driving",
    )

    assert result["route_geometry_proven"] is True
    assert result["provider_ownership"] == "oap_owned"
    assert result["geometry"]["type"] == "LineString"
    assert len(result["geometry_sha256"]) == 64
    assert result["dispatch_performed"] is False
    assert result["payment_captured"] is False
    assert result["tracking_started"] is False
    assert result["booking_confirmed"] is False
    assert "geometries=geojson" in captured["url"]
    assert captured["host"] == "routes.oap.invalid"


def test_first_party_route_proof_rejects_missing_geometry(monkeypatch):
    monkeypatch.setattr(route_proof.routing, "provider_ownership", lambda: "oap_owned")
    monkeypatch.setattr(route_proof.routing, "production_gate_approved", lambda: True)
    monkeypatch.setattr(
        route_proof.routing,
        "_base_url",
        lambda: "https://routes.oap.invalid",
    )
    monkeypatch.setattr(
        route_proof.routing,
        "_request_json",
        lambda *_args, **_kwargs: {
            "code": "Ok",
            "routes": [{"distance": 1, "duration": 1}],
        },
    )

    with pytest.raises(route_proof.RouteProofUnavailable, match="route_geometry_required"):
        route_proof.prove_route_geometry(
            pickup_latitude=51.403,
            pickup_longitude=-0.168,
            destination_latitude=51.505,
            destination_longitude=-0.118,
        )
