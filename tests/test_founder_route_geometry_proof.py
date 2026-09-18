from __future__ import annotations

from mission_control import movement_routes


def test_founder_route_geometry_proof_returns_first_party_result(app, client, monkeypatch):
    monkeypatch.setattr(
        movement_routes.web_security,
        "authenticated_identity",
        lambda: "00000000-0000-0000-0000-000000000001",
    )
    monkeypatch.setattr(
        movement_routes.first_party_route_proof,
        "prove_route_geometry",
        lambda **kwargs: {
            "component": "OAP Map Intelligence Route Proof",
            "profile": "driving",
            "distance_m": 12345.6,
            "duration_s": 1400.0,
            "geometry": {"type": "LineString", "coordinates": [[-0.1687, 51.4036], [-0.0877, 51.5079]]},
            "geometry_sha256": "a" * 64,
            "provider_ownership": "oap_owned",
            "route_geometry_proven": True,
            "dispatch_performed": False,
            "payment_captured": False,
            "tracking_started": False,
            "booking_confirmed": False,
        },
    )
    monkeypatch.setattr(
        movement_routes.web_security,
        "login_required",
        lambda *args, **kwargs: (lambda fn: fn),
    )

    with app.test_request_context(
        "/mission/movement/route-geometry-proof?from_lat=51.4036&from_lon=-0.1687&to_lat=51.5079&to_lon=-0.0877"
    ):
        response = movement_routes.founder_route_geometry_proof()

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["route_geometry_proven"] is True
    assert payload["provider_ownership"] == "oap_owned"
    assert payload["geometry"]["type"] == "LineString"
    assert payload["dispatch_performed"] is False
    assert payload["payment_captured"] is False
