from __future__ import annotations

from mission_control import humanitarian_emergency_tracker, humanitarian_views


def _gdacs_event():
    return {
        "source": "gdacs",
        "source_event_id": "gd-1",
        "category": "natural_hazard",
        "event_type": "EQ",
        "name": "Earthquake",
        "alert_level": "Red",
        "countries": ("Exampleland",),
        "from_date": "2026-09-04T01:00:00Z",
        "to_date": "2026-09-04T02:00:00Z",
        "geometry": {"latitude": 10.123, "longitude": 20.456},
        "civilian_only": True,
        "targeting": False,
        "surveillance": False,
    }


def _who_event():
    return {
        "source": "who_don",
        "source_event_id": "who-1",
        "category": "health",
        "event_type": "WHO_DON",
        "name": "Disease outbreak update",
        "alert_level": "WHO Update",
        "countries": ("Exampleland",),
        "from_date": "2026-09-04T03:00:00Z",
        "to_date": None,
        "geometry": None,
        "summary": "Authoritative public-health update.",
        "civilian_only": True,
        "targeting": False,
        "surveillance": False,
    }


def test_tracker_architecture_is_multi_source_civilian_and_non_executing():
    status = humanitarian_emergency_tracker.humanitarian_emergency_tracker_status()

    assert status["architecture_ready"] is True
    assert status["source_count"] == 4
    assert status["gdacs_live_fetch_enabled"] is True
    assert status["who_live_fetch_enabled"] is True
    assert status["unhcr_live_context_enabled"] is True
    assert status["reliefweb_preapproved_appname_required"] is True
    assert status["matrix_world_state_ready"] is True
    assert status["founder_dashboard_ready"] is True
    assert status["smi_context_ready"] is True
    assert status["civilian_only"] is True
    assert status["precise_civilian_location_public"] is False
    assert status["individual_tracking"] is False
    assert status["military_overlays"] is False
    assert status["targeting"] is False
    assert status["surveillance"] is False
    assert status["autonomous_dispatch"] is False
    assert status["autonomous_public_warning"] is False
    assert status["human_authority_final"] is True


def test_who_outbreak_adapter_normalises_without_inventing_severity(monkeypatch):
    payload = {
        "value": [
            {
                "DonId": "who-77",
                "Title": "Outbreak update",
                "PublicationDate": "2026-09-04T06:00:00Z",
                "Summary": "<p>Confirmed public health information.</p>",
                "countries": ["Exampleland"],
            }
        ]
    }
    monkeypatch.setattr(humanitarian_emergency_tracker, "_fetch_json", lambda _url: payload)

    result = humanitarian_emergency_tracker.fetch_who_outbreaks()

    assert result["live"] is True
    assert result["event_count"] == 1
    event = result["events"][0]
    assert event["source"] == "who_don"
    assert event["category"] == "health"
    assert event["alert_level"] == "WHO Update"
    assert event["summary"] == "Confirmed public health information."
    assert event["targeting"] is False
    assert event["surveillance"] is False


def test_multi_source_snapshot_prepares_privacy_reduced_matrix_events(monkeypatch):
    monkeypatch.setattr(
        humanitarian_emergency_tracker.world_crisis_intelligence,
        "fetch_gdacs_crises",
        lambda: {
            "source": "gdacs",
            "live": True,
            "error": None,
            "event_count": 1,
            "events": (_gdacs_event(),),
            "fetched_at": "2026-09-04T07:00:00Z",
        },
    )
    monkeypatch.setattr(
        humanitarian_emergency_tracker,
        "fetch_who_outbreaks",
        lambda: {
            "source": "who_don",
            "live": True,
            "error": None,
            "event_count": 1,
            "events": (_who_event(),),
            "fetched_at": "2026-09-04T07:00:00Z",
        },
    )
    monkeypatch.setattr(
        humanitarian_emergency_tracker,
        "fetch_unhcr_displacement_context",
        lambda: {
            "source": "unhcr_nowcasting",
            "live": True,
            "error": None,
            "row_count": 2,
            "latest_year": 2026,
            "fetched_at": "2026-09-04T07:00:00Z",
        },
    )

    snapshot = humanitarian_emergency_tracker.humanitarian_emergency_snapshot(force=True)

    assert snapshot["tracking_ready"] is True
    assert set(snapshot["live_sources"]) == {"gdacs", "who_don", "unhcr_nowcasting"}
    assert snapshot["event_count"] == 2
    assert snapshot["category_counts"] == {"natural_hazard": 1, "health": 1}
    assert len(snapshot["matrix_events"]) == 2
    matrix_event = snapshot["matrix_events"][0]
    assert matrix_event["civilian_only"] is True
    assert matrix_event["precise_civilian_location"] is False
    assert matrix_event["targeting"] is False
    assert matrix_event["surveillance"] is False
    assert "summary" not in matrix_event
    assert snapshot["autonomous_dispatch"] is False
    assert snapshot["autonomous_public_warning"] is False


def test_source_failure_does_not_create_fake_event(monkeypatch):
    def fail(_url):
        raise TimeoutError("offline")

    monkeypatch.setattr(humanitarian_emergency_tracker, "_fetch_json", fail)
    who = humanitarian_emergency_tracker.fetch_who_outbreaks()
    unhcr = humanitarian_emergency_tracker.fetch_unhcr_displacement_context()

    assert who["live"] is False
    assert who["event_count"] == 0
    assert who["events"] == ()
    assert who["error"] == "TimeoutError"
    assert unhcr["live"] is False
    assert unhcr["row_count"] == 0
    assert unhcr["error"] == "TimeoutError"


def test_founder_dashboard_renders_source_and_guardian_boundaries(client, monkeypatch):
    snapshot = {
        "tracking_ready": True,
        "live_source_count": 2,
        "event_count": 1,
        "cache_seconds": 180,
        "source_states": {
            "gdacs": {"live": True, "fetched_at": "now", "event_count": 1, "error": None},
            "who_don": {"live": True, "fetched_at": "now", "event_count": 0, "error": None},
            "unhcr_nowcasting": {"live": False, "fetched_at": "now", "row_count": 0, "error": "empty_response"},
            "reliefweb": {"live": False, "configured": False, "error": "preapproved_appname_required"},
        },
        "category_counts": {"natural_hazard": 1},
        "events": (_gdacs_event(),),
        "country_counts": ({"country": "Exampleland", "event_count": 1},),
        "matrix_events": ({"event_type": "humanitarian_emergency_signal"},),
    }
    monkeypatch.setattr(
        humanitarian_views.humanitarian_emergency_tracker,
        "humanitarian_emergency_snapshot",
        lambda: snapshot,
    )

    response = client.get("/mission/humanitarian")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Humanitarian Emergency Tracker" in page
    assert "Live humanitarian tracking active" in page
    assert "no military overlays" in page
    assert "no target lists" in page
    assert "Matrix-ready humanitarian world state" in page
