from __future__ import annotations

import pytest

from mission_control import first_party_route_proof, routing


def _owned_ready(monkeypatch):
    monkeypatch.setattr(routing, "provider_ownership", lambda: "oap_owned")
    monkeypatch.setattr(routing, "production_gate_approved", lambda: True)
    monkeypatch.setattr(
        routing,
        "production_approval_state",
        lambda: {
            "provider_approved": True,
            "capacity_approved": True,
            "monitoring_approved": True,
        },
    )
    monkeypatch.setattr(routing, "_base_url", lambda: "https://route.oap.test")


def test_external_route_provider_cannot_satisfy_first_party_proof(monkeypatch):
    monkeypatch.setattr(routing, "provider_ownership", lambda: "external_candidate")

    with pytest.raises(
        first_party_route_proof.RouteProofUnavailable,
        match="oap_owned_route_engine_required",
    ):
        first_party_route_proof.prove(
            pickup_latitude=51.4,
            pickup_longitude=-0.16,
            destination_latitude=51.5,
            destination_longitude=-0.09,
        )


def test_owned_route_geometry_returns_timestamped_checksum_proof(monkeypatch):
    _owned_ready(monkeypatch)
    monkeypatch.setattr(
        routing,
        "_request_json",
        lambda _url, expected_host: {
            "code": "Ok",
            "routes": [
                {
                    "distance": 13500.4,
                    "duration": 2440.2,
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [-0.16, 51.4],
                            [-0.13, 51.44],
                            [-0.09, 51.5],
                        ],
                    },
                }
            ],
        },
    )

    proof = first_party_route_proof.prove(
        pickup_latitude=51.4,
        pickup_longitude=-0.16,
        destination_latitude=51.5,
        destination_longitude=-0.09,
        profile="driving",
    )

    assert proof["proof_state"] == "PROVEN"
    assert proof["provider_ownership"] == "oap_owned"
    assert proof["geometry"]["type"] == "LineString"
    assert proof["geometry_point_count"] == 3
    assert len(proof["geometry_checksum_sha256"]) == 64
    assert proof["source_timestamp"].endswith("Z")
    assert proof["third_party_route_api_used"] is False
    assert proof["payment_capture"] is False
    assert proof["dispatch_performed"] is False
    assert proof["hidden_tracking"] is False


def test_owned_endpoint_without_production_evidence_stays_locked(monkeypatch):
    monkeypatch.setattr(routing, "provider_ownership", lambda: "oap_owned")
    monkeypatch.setattr(routing, "production_gate_approved", lambda: False)

    with pytest.raises(
        first_party_route_proof.RouteProofUnavailable,
        match="oap_route_engine_production_gate_required",
    ):
        first_party_route_proof.prove(
            pickup_latitude=51.4,
            pickup_longitude=-0.16,
            destination_latitude=51.5,
            destination_longitude=-0.09,
        )


def test_status_never_claims_third_party_geometry_ready(monkeypatch):
    monkeypatch.setattr(routing, "provider_ownership", lambda: "verification_only")
    monkeypatch.setattr(routing, "production_gate_approved", lambda: False)
    monkeypatch.setattr(
        routing,
        "production_approval_state",
        lambda: {
            "provider_approved": False,
            "capacity_approved": False,
            "monitoring_approved": False,
        },
    )

    status = first_party_route_proof.status()

    assert status["geometry_proof_ready"] is False
    assert status["third_party_route_api_allowed_for_proof"] is False
    assert status["dispatch_enabled"] is False
    assert status["payment_capture_enabled"] is False
