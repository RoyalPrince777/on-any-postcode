from __future__ import annotations

from mission_control import humanitarian_pulse


def _snapshot():
    return {
        "events": (
            {
                "source": "gdacs",
                "source_event_id": "1001",
                "category": "natural_hazard",
                "event_type": "EQ",
                "name": "Earthquake",
                "alert_level": "Red",
                "countries": ("Country A",),
                "from_date": "2026-09-13",
                "summary": "",
                "geometry": {"latitude": 1.234, "longitude": 2.345},
                "civilian_only": True,
                "targeting": False,
                "surveillance": False,
            },
            {
                "source": "who_don",
                "source_event_id": "don-1",
                "category": "health",
                "event_type": "WHO_DON",
                "name": "Disease outbreak update",
                "alert_level": "WHO Update",
                "countries": ("Country B",),
                "from_date": "2026-09-12",
                "summary": "Public-health source summary.",
                "source_url": "/emergencies/disease-outbreak-news/item/example",
                "civilian_only": True,
                "targeting": False,
                "surveillance": False,
            },
            {
                "source": "unknown_feed",
                "source_event_id": "bad-1",
                "name": "Unsupported",
                "civilian_only": True,
            },
            {
                "source": "gdacs",
                "source_event_id": "unsafe-1",
                "event_type": "FL",
                "name": "Unsafe",
                "civilian_only": True,
                "targeting": True,
            },
        ),
        "live_sources": ("gdacs", "who_don", "unhcr_nowcasting"),
        "source_states": {
            "gdacs": {"live": True},
            "who_don": {"live": True},
            "unhcr_nowcasting": {"live": True},
            "reliefweb": {
                "live": False,
                "configured": False,
                "error": "preapproved_appname_required",
            },
        },
        "fetched_at": "2026-09-13T22:00:00+00:00",
        "cache_seconds": 180,
    }


def test_public_projection_is_source_backed_privacy_reduced_and_world_typed(monkeypatch):
    monkeypatch.setattr(
        humanitarian_pulse.humanitarian_emergency_tracker,
        "humanitarian_emergency_snapshot",
        lambda **_kwargs: _snapshot(),
    )

    result = humanitarian_pulse.public_snapshot()

    assert result["ready"] is True
    assert result["event_count"] == 2
    assert tuple(item["source"] for item in result["events"]) == ("gdacs", "who_don")
    assert result["events"][0]["world_disaster_type"] == "earthquake"
    assert result["events"][0]["world_disaster_label"] == "Earthquakes"
    assert result["events"][0]["world_disaster_icon"] == "🌎"
    assert result["events"][0]["affected_area"] == "Country A"
    assert result["events"][0]["severity"] == "Red"
    assert result["events"][0]["truth"] == "Observed source record"
    assert result["events"][1]["world_disaster_type"] == "health"
    assert "geometry" not in result["events"][0]
    assert result["events"][1]["source_url"].startswith("https://www.who.int/")
    assert result["precise_civilian_location"] is False
    assert result["individual_tracking"] is False
    assert result["autonomous_warning"] is False
    assert next(
        item for item in result["source_states"] if item["source"] == "reliefweb"
    )["status"] == "gated"

    categories = {item["id"]: item for item in result["disaster_categories"]}
    assert tuple(categories) == (
        "flood",
        "volcano",
        "earthquake",
        "wildfire",
        "drought",
        "cyclone",
        "health",
    )
    assert categories["earthquake"]["count"] == 1
    assert categories["health"]["count"] == 1
    assert categories["flood"]["count"] == 0


def test_gdacs_event_codes_map_only_to_locked_world_disaster_types():
    expected = {
        "FL": "flood",
        "VO": "volcano",
        "EQ": "earthquake",
        "WF": "wildfire",
        "DR": "drought",
        "TC": "cyclone",
    }
    for event_type, disaster_type in expected.items():
        projected = humanitarian_pulse._event_projection(
            {
                "source": "gdacs",
                "source_event_id": f"source-{event_type}",
                "event_type": event_type,
                "name": event_type,
                "alert_level": "Orange",
                "countries": ("Country",),
                "civilian_only": True,
                "targeting": False,
                "surveillance": False,
            }
        )
        assert projected is not None
        assert projected["world_disaster_type"] == disaster_type

    assert humanitarian_pulse._event_projection(
        {
            "source": "gdacs",
            "source_event_id": "unknown",
            "event_type": "XX",
            "name": "Unknown",
            "civilian_only": True,
        }
    ) is None


def test_public_projection_fails_closed_when_tracker_raises(monkeypatch):
    def fail(**_kwargs):
        raise RuntimeError("source down")

    monkeypatch.setattr(
        humanitarian_pulse.humanitarian_emergency_tracker,
        "humanitarian_emergency_snapshot",
        fail,
    )

    result = humanitarian_pulse.public_snapshot()

    assert result["ready"] is False
    assert result["events"] == ()
    assert result["event_count"] == 0
    assert len(result["disaster_categories"]) == 7
    assert all(item["count"] == 0 for item in result["disaster_categories"])
    assert result["source_backed_only"] is True
    assert result["precise_civilian_location"] is False


def test_refresh_interval_is_bounded(monkeypatch):
    snapshot = _snapshot()
    snapshot["cache_seconds"] = 10_000
    monkeypatch.setattr(
        humanitarian_pulse.humanitarian_emergency_tracker,
        "humanitarian_emergency_snapshot",
        lambda **_kwargs: snapshot,
    )
    assert humanitarian_pulse.public_snapshot()["refresh_seconds"] == 900

    snapshot["cache_seconds"] = 1
    assert humanitarian_pulse.public_snapshot()["refresh_seconds"] == 60
