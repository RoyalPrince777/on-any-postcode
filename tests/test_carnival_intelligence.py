from __future__ import annotations

import json
from datetime import datetime

import pytest

from mission_control import carnival_intelligence


def test_carnival_hub_is_bounded_to_reviewed_scheduled_sources():
    validation = carnival_intelligence.validate_carnival_hub()

    assert validation == {
        "passed": True,
        "errors": [],
        "checks": {
            "official_sources": 7,
            "schedule_days": 3,
            "public_layers": 7,
            "travel_alerts": 6,
            "runtime_provider_calls": 0,
            "live_feeds": 0,
        },
    }
    assert all(
        item["claim"] == "scheduled"
        for day in carnival_intelligence.SCHEDULE
        for item in day["items"]
    )
    assert all(
        value is False for value in carnival_intelligence.PUBLIC_BOUNDARY.values()
    )


def test_carnival_validation_fails_closed_for_unapproved_or_live_claims():
    unsafe_sources = (
        *carnival_intelligence.SOURCES[:-1],
        {
            "id": "nhc-accessibility",
            "name": "Unreviewed event feed",
            "url": "https://example.com/live-crowds",
            "publisher": "Unknown",
            "source_updated_on": "Now",
            "reviewed_on": "2026-08-28",
        },
    )
    unsafe_schedule = tuple(
        {
            **day,
            "items": tuple(
                {**item, "claim": "live"}
                if item["name"] == "Parade begins"
                else item
                for item in day["items"]
            ),
        }
        for day in carnival_intelligence.SCHEDULE
    )
    unsafe_map = {**carnival_intelligence.MAP, "loads_automatically": True}
    unsafe_boundary = {
        **carnival_intelligence.PUBLIC_BOUNDARY,
        "live_child_tracking": True,
    }

    source_result = carnival_intelligence.validate_carnival_hub(
        sources=unsafe_sources
    )
    schedule_result = carnival_intelligence.validate_carnival_hub(
        schedule=unsafe_schedule
    )
    map_result = carnival_intelligence.validate_carnival_hub(map_config=unsafe_map)
    boundary_result = carnival_intelligence.validate_carnival_hub(
        public_boundary=unsafe_boundary
    )

    assert source_result["passed"] is False
    assert any("Unapproved Carnival source" in item for item in source_result["errors"])
    assert schedule_result["passed"] is False
    assert any("mislabelled as live" in item for item in schedule_result["errors"])
    assert map_result["passed"] is False
    assert "The public map must be opt-in and location-free" in map_result["errors"]
    assert boundary_result["passed"] is False
    assert "Carnival v0 must remain read-only and tracking-free" in boundary_result[
        "errors"
    ]


def test_event_phase_expires_closed_and_requires_timezone():
    london = carnival_intelligence.EVENT_TIMEZONE

    scheduled = carnival_intelligence.get_public_carnival_hub(
        datetime(2026, 8, 29, 10, 59, tzinfo=london)
    )
    event_window = carnival_intelligence.get_public_carnival_hub(
        datetime(2026, 8, 30, 12, 0, tzinfo=london)
    )
    archive = carnival_intelligence.get_public_carnival_hub(
        datetime(2026, 9, 1, 6, 1, tzinfo=london)
    )

    assert scheduled["event"]["phase"]["id"] == "scheduled"
    assert event_window["event"]["phase"]["id"] == "event-window"
    assert "no verified live feed" in event_window["event"]["phase"]["message"]
    assert archive["event"]["phase"]["id"] == "archive"
    assert "Do not use these details for travel" in archive["event"]["phase"][
        "message"
    ]
    with pytest.raises(ValueError, match="timezone_required"):
        carnival_intelligence.get_public_carnival_hub(
            datetime.fromisoformat("2026-08-30T12:00:00")
        )


def test_carnival_routes_are_public_read_only_and_truthful(anonymous_client):
    for path in ("/carnival", "/world/carnival", "/the-spot/carnival"):
        response = anonymous_client.get(path)
        page = response.get_data(as_text=True)

        assert response.status_code == 200
        assert response.headers["Cache-Control"] == "no-store"
        assert "Carnival Intelligence" in page
        assert "Official scheduled sources · no live feed" in page
        assert "Official schedule · not live telemetry" in page
        assert "No attendee, child, crew or officer tracking" in page
        assert "A person makes the final decision" in page
        assert anonymous_client.post(path).status_code == 405


def test_map_is_explicit_opt_in_with_route_scoped_security(anonymous_client):
    response = anonymous_client.get("/world/carnival")
    page = response.get_data(as_text=True)
    policy = response.headers["Content-Security-Policy"]

    assert "Load OpenStreetMap" in page
    assert "data-oap-map" in page
    assert "<iframe" not in page.casefold()
    assert "carnival_intelligence.js" in page
    assert "frame-src https://www.openstreetmap.org" in policy
    assert "connect-src 'self'" in policy
    assert "script-src 'self'" in policy
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert "geolocation=()" in response.headers["Permissions-Policy"]

    script = anonymous_client.get(
        "/static/carnival_intelligence.js"
    ).get_data(as_text=True)
    assert 'mapUrl.hostname === "www.openstreetmap.org"' in script
    assert 'mapUrl.pathname === "/export/embed.html"' in script
    assert "navigator.geolocation" not in script
    assert "localStorage" not in script


def test_public_projection_contains_no_person_or_runtime_tracking_data():
    hub = carnival_intelligence.get_public_carnival_hub(
        datetime(2026, 8, 29, 12, tzinfo=carnival_intelligence.EVENT_TIMEZONE)
    )
    serialized = json.dumps(hub).casefold()

    assert hub["live_feed_available"] is False
    assert hub["map"]["loads_automatically"] is False
    assert hub["map"]["uses_device_location"] is False
    assert all(value is False for value in hub["boundary"].values())
    for private_key in (
        "member_id",
        "email_address",
        "device_id",
        "precise_coordinates",
        "officer_position",
        "child_position",
        "face_embedding",
        "route_history",
        "auth_token",
    ):
        assert private_key not in serialized


def test_welfare_and_travel_guidance_stays_source_linked():
    hub = carnival_intelligence.get_public_carnival_hub(
        datetime(2026, 8, 29, 12, tzinfo=carnival_intelligence.EVENT_TIMEZONE)
    )

    assert set(hub["welfare_locations"]) == {
        "Powis Square",
        "Emslie Horniman’s Pleasance Gardens (north end)",
        "Shrewsbury Gardens",
        "Venture Community Centre, Faraday Road",
    }
    assert all(item["source_id"] in hub["sources_by_id"] for item in hub["layers"])
    assert all(
        item["source_id"] in hub["sources_by_id"] for item in hub["travel_alerts"]
    )
    assert hub["sources_by_id"]["rbkc-event-map"]["source_updated_on"] == (
        "2026-08-28"
    )
