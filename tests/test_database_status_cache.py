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
    monkeypatch.delenv("OAP_LOCAL_MODE", raising=False)
    monkeypatch.setattr(database.postgres_db, "configured", lambda: True)

    calls = []

    def fake_status():
        calls.append(len(calls) + 1)
        return _status()

    monkeypatch.setattr(database.postgres_db, "postgres_status", fake_status)

    database.db_status()
    database.db_status()

    assert calls == [1, 2]


def test_local_termux_readiness_cache_is_bounded_to_five_seconds(monkeypatch):
    database._clear_db_status_cache()
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.setenv("OAP_LOCAL_MODE", "true")
    monkeypatch.setenv("OAP_DB_STATUS_CACHE_SECONDS", "300")
    monkeypatch.setattr(database.postgres_db, "configured", lambda: True)
    calls = []
    clock = {"now": 10.0}
    monkeypatch.setattr(database.time, "monotonic", lambda: clock["now"])
    monkeypatch.setattr(
        database.postgres_db, "postgres_status",
        lambda: calls.append("probe") or _status(),
    )

    assert database.db_status()["reachable"]
    assert database.db_status()["reachable"]
    assert calls == ["probe"]
    clock["now"] = 15.1
    assert database.db_status()["reachable"]
    assert calls == ["probe", "probe"]


def test_local_readiness_cache_does_not_promote_unreachable_database(monkeypatch):
    database._clear_db_status_cache()
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.setenv("OAP_LOCAL_MODE", "true")
    monkeypatch.setattr(database.postgres_db, "configured", lambda: True)
    monkeypatch.setattr(database.time, "monotonic", lambda: 3.0)
    monkeypatch.setattr(
        database.postgres_db, "postgres_status",
        lambda: _status(reachable=False, initialized=False, pending=["missing"]),
    )
    first = database.db_status()
    second = database.db_status()
    assert not first["reachable"] and not first["initialized"]
    assert not second["reachable"] and not second["initialized"]


def test_local_cache_is_disabled_without_explicit_local_mode(monkeypatch):
    database._clear_db_status_cache()
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("OAP_LOCAL_MODE", raising=False)
    monkeypatch.setattr(database.postgres_db, "configured", lambda: True)
    calls = []
    monkeypatch.setattr(
        database.postgres_db, "postgres_status",
        lambda: calls.append(1) or _status(),
    )
    database.db_status()
    database.db_status()
    assert calls == [1, 1]
