from __future__ import annotations

from mission_control import humanitarian_pulse


def _snapshot():
    return {
        "events": (
            {
                "source": "gdacs",
                "source_event_id": "1001",
                "category": "natural_hazard",
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


def test_public_projection_is_source_backed_and_privacy_reduced(monkeypatch):
    monkeypatch.setattr(
        humanitarian_pulse.humanitarian_emergency_tracker,
        "humanitarian_emergency_snapshot",
        lambda **_kwargs: _snapshot(),
    )

    result = humanitarian_pulse.public_snapshot()

    assert result["ready"] is True
    assert result["event_count"] == 2
    assert tuple(item["source"] for item in result["events"]) == ("gdacs", "who_don")
    assert result["events"][0]["truth"] == "Observed source record"
    assert "geometry" not in result["events"][0]
    assert result["events"][1]["source_url"].startswith("https://www.who.int/")
    assert result["precise_civilian_location"] is False
    assert result["individual_tracking"] is False
    assert result["autonomous_warning"] is False
    assert next(
        item for item in result["source_states"] if item["source"] == "reliefweb"
    )["status"] == "gated"


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
