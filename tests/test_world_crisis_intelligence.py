from datetime import UTC, datetime

from mission_control import world_crisis_intelligence


def test_world_crisis_architecture_is_live_civilian_and_non_executing():
    status = world_crisis_intelligence.world_crisis_intelligence_status()

    assert status["name"] == "World Crisis Emergency Intelligence"
    assert status["parent"] == "International Humanitarian Intelligence"
    assert status["mode"] == "live_civilian_crisis_awareness"
    assert status["demo_mode"] is False
    assert status["architecture_ready"] is True
    assert status["category_count"] == 8
    assert status["source_count"] == 4
    assert status["live_machine_source_enabled"] == "gdacs"
    assert status["map_ready"] is True
    assert status["legal_intelligence_bound"] is True
    assert status["civilian_only"] is True
    assert status["precise_civilian_location_public"] is False
    assert status["individual_tracking"] is False
    assert status["military_overlays"] is False
    assert status["targeting"] is False
    assert status["surveillance"] is False
    assert status["autonomous_dispatch"] is False
    assert status["autonomous_broadcast"] is False
    assert status["independent_execute"] is False
    assert status["independent_approval"] is False
    assert status["human_authority_final"] is True


def test_live_gdacs_snapshot_normalises_orange_and_red_events(monkeypatch):
    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [10.12349, 20.98761]},
                "properties": {
                    "eventid": 777,
                    "eventtype": "EQ",
                    "name": "Earthquake test event",
                    "alertlevel": "Red",
                    "alertscore": 2.5,
                    "country": "Exampleland",
                    "fromdate": "2026-09-03T00:00:00Z",
                    "todate": "2026-09-04T00:00:00Z",
                },
            },
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [1, 2]},
                "properties": {
                    "eventid": 778,
                    "eventtype": "FL",
                    "name": "Flood test event",
                    "alertlevel": "Orange",
                    "country": "Exampleland",
                },
            },
        ],
    }

    monkeypatch.setattr(
        world_crisis_intelligence,
        "_fetch_json",
        lambda _url, timeout: payload,
    )
    result = world_crisis_intelligence.fetch_gdacs_crises(
        now=datetime(2026, 9, 4, tzinfo=UTC)
    )

    assert result["live"] is True
    assert result["event_count"] == 2
    assert result["events"][0]["alert_level"] == "Red"
    assert result["events"][0]["category"] == "natural_hazard"
    assert result["events"][0]["geometry"] == {
        "latitude": 20.988,
        "longitude": 10.123,
    }
    assert result["events"][0]["targeting"] is False
    assert result["events"][0]["surveillance"] is False


def test_source_failure_fails_closed_without_fake_crisis_data(monkeypatch):
    def fail(_url, *, timeout):
        raise TimeoutError("source unavailable")

    monkeypatch.setattr(world_crisis_intelligence, "_fetch_json", fail)
    result = world_crisis_intelligence.fetch_gdacs_crises(
        now=datetime(2026, 9, 4, tzinfo=UTC)
    )

    assert result["live"] is False
    assert result["event_count"] == 0
    assert result["events"] == ()
    assert result["error"] == "TimeoutError"


def test_world_crisis_snapshot_never_claims_live_when_fetch_disabled():
    result = world_crisis_intelligence.world_crisis_snapshot(live_fetch=False)

    assert result["demo_mode"] is False
    assert result["live_data_ready"] is False
    assert result["live_source_count"] == 0
    assert result["event_count"] == 0
    assert result["autonomous_dispatch"] is False
    assert result["autonomous_broadcast"] is False
    assert result["human_authority_final"] is True
