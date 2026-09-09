from mission_control import database


def _status(*, reachable=True, initialized=True, pending=None):
    return {
        "backend": "postgresql",
        "configured": True,
        "reachable": reachable,
        "initialized": initialized,
        "pending": list(pending or ()),
        "checksum_mismatches": [],
        "error": None,
    }


def test_render_database_status_is_cached_and_expires(monkeypatch):
    database._clear_db_status_cache()
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("OAP_DB_STATUS_CACHE_SECONDS", "60")
    monkeypatch.setattr(database.postgres_db, "configured", lambda: True)

    calls = []

    def fake_status():
        calls.append(len(calls) + 1)
        return _status()

    clock = {"now": 100.0}
    monkeypatch.setattr(database.time, "monotonic", lambda: clock["now"])
    monkeypatch.setattr(database.postgres_db, "postgres_status", fake_status)

    first = database.db_status()
    second = database.db_status()

    assert first["reachable"] is True
    assert second["reachable"] is True
    assert calls == [1]

    clock["now"] = 161.0
    third = database.db_status()

    assert third["reachable"] is True
    assert calls == [1, 2]


def test_render_database_status_caches_fail_closed_result(monkeypatch):
    database._clear_db_status_cache()
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setattr(database.postgres_db, "configured", lambda: True)

    calls = []

    def fake_status():
        calls.append(len(calls) + 1)
        return {
            **_status(reachable=False, initialized=False, pending=(database.postgres_db.MIGRATION_VERSION,)),
            "error": "database_unavailable",
        }

    monkeypatch.setattr(database.time, "monotonic", lambda: 200.0)
    monkeypatch.setattr(database.postgres_db, "postgres_status", fake_status)

    first = database.db_status()
    second = database.db_status()

    assert first["exists"] is False
    assert second["exists"] is False
    assert first["error"] == "database_unavailable"
    assert calls == [1]


def test_non_render_database_status_remains_live(monkeypatch):
    database._clear_db_status_cache()
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.setattr(database.postgres_db, "configured", lambda: True)

    calls = []

    def fake_status():
        calls.append(len(calls) + 1)
        return _status()

    monkeypatch.setattr(database.postgres_db, "postgres_status", fake_status)

    database.db_status()
    database.db_status()

    assert calls == [1, 2]
