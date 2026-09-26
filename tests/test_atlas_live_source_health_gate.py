from datetime import datetime, timedelta, timezone

from mission_control import atlas_live_sources


def _stamp(seconds_ago: int = 0) -> str:
    return (datetime.now(timezone.utc) - timedelta(seconds=seconds_ago)).isoformat().replace("+00:00", "Z")


def test_environment_switch_alone_never_allows_live_claim(monkeypatch):
    monkeypatch.setenv("OAP_ATLAS_OPEN_DATA_ENABLED", "true")
    atlas_live_sources._LAST_FETCH.update(
        fetched_at=None,
        fetch_status="unseen",
        result_count=0,
        source_backed=False,
        query_recorded=False,
    )
    status = atlas_live_sources.status()
    assert status["enabled"] is True
    assert status["live_claim_allowed"] is False
    assert status["state"] == "enabled_unproven"
    assert status["signal"] == "yellow"


def test_fresh_successful_source_health_allows_bounded_live_claim(monkeypatch):
    monkeypatch.setenv("OAP_ATLAS_OPEN_DATA_ENABLED", "true")
    atlas_live_sources._LAST_FETCH.update(
        fetched_at=_stamp(),
        fetch_status="success",
        result_count=2,
        source_backed=True,
        query_recorded=True,
    )
    status = atlas_live_sources.status()
    assert status["live_claim_allowed"] is True
    assert status["state"] == "source_proven"
    assert status["signal"] == "green"
    assert status["last_fetch"]["freshness"] == "fresh"


def test_stale_or_failed_source_health_fails_closed(monkeypatch):
    monkeypatch.setenv("OAP_ATLAS_OPEN_DATA_ENABLED", "true")
    atlas_live_sources._LAST_FETCH.update(
        fetched_at=_stamp(atlas_live_sources.FRESH_SECONDS + 5),
        fetch_status="success",
        result_count=2,
        source_backed=True,
        query_recorded=True,
    )
    stale = atlas_live_sources.status()
    assert stale["last_fetch"]["freshness"] == "stale"
    assert stale["live_claim_allowed"] is False

    atlas_live_sources._LAST_FETCH.update(
        fetched_at=_stamp(),
        fetch_status="failed_safe",
        result_count=0,
        source_backed=False,
        query_recorded=True,
    )
    failed = atlas_live_sources.status()
    assert failed["live_claim_allowed"] is False
    assert failed["signal"] == "yellow"
