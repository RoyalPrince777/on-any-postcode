from __future__ import annotations

from mission_control import first_party_route_proof, routing


def test_first_party_route_surface_is_read_only_and_locked_without_owned_engine(
    client, monkeypatch
):
    monkeypatch.setattr(routing, "provider_ownership", lambda: "external_candidate")

    response = client.get(
        "/on-any-route/proof?from_lat=51.4&from_lon=-0.16&to_lat=51.5&to_lon=-0.09"
    )
    payload = response.get_json()

    assert response.status_code == 503
    assert response.headers["Cache-Control"] == "no-store"
    assert payload["state"] == "LOCKED"
    assert payload["third_party_route_api_used"] is False
    assert payload["dispatch_performed"] is False
    assert payload["payment_capture"] is False
    assert client.post("/on-any-route/proof").status_code == 405


def test_first_party_route_surface_returns_only_proven_owned_geometry(
    client, monkeypatch
):
    monkeypatch.setattr(
        first_party_route_proof,
        "prove",
        lambda **_kwargs: {
            "proof_state": "PROVEN",
            "provider_ownership": "oap_owned",
            "geometry": {
                "type": "LineString",
                "coordinates": [[-0.16, 51.4], [-0.09, 51.5]],
            },
            "geometry_checksum_sha256": "a" * 64,
            "source_timestamp": "2026-09-15T21:00:00Z",
            "third_party_route_api_used": False,
            "dispatch_performed": False,
            "payment_capture": False,
            "hidden_tracking": False,
        },
    )

    response = client.get(
        "/on-any-route/proof?from_lat=51.4&from_lon=-0.16&to_lat=51.5&to_lon=-0.09"
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["proof_state"] == "PROVEN"
    assert payload["provider_ownership"] == "oap_owned"
    assert payload["third_party_route_api_used"] is False
