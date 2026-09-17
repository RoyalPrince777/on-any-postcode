from mission_control import esim_provisioning, esim_runtime


class _Result:
    def __init__(self, row):
        self._row = row

    def fetchone(self):
        return self._row


class _Connection:
    def __init__(self, row):
        self._row = row

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, statement, params):
        assert "to_regclass" in statement
        assert params == ("oap_esim_requests", "oap_esim_events")
        return _Result(self._row)


def teardown_function():
    esim_provisioning.CORE.repository = None


def test_runtime_fails_closed_without_database(monkeypatch):
    monkeypatch.setattr(esim_runtime.postgres_db, "configured", lambda: False)

    status = esim_runtime.configure()

    assert status == {
        "persistence_attached": False,
        "database_configured": False,
        "schema_ready": False,
        "reason": "database_not_configured",
    }


def test_runtime_requires_existing_esim_schema(monkeypatch):
    monkeypatch.setattr(esim_runtime.postgres_db, "configured", lambda: True)
    monkeypatch.setattr(
        esim_runtime.postgres_db,
        "connect",
        lambda: _Connection(("oap_esim_requests", None)),
    )

    status = esim_runtime.configure()

    assert status["persistence_attached"] is False
    assert status["schema_ready"] is False
    assert status["reason"] == "esim_schema_not_initialized"


def test_runtime_attaches_repository_only_after_schema_exists(monkeypatch):
    monkeypatch.setattr(esim_runtime.postgres_db, "configured", lambda: True)
    monkeypatch.setattr(
        esim_runtime.postgres_db,
        "connect",
        lambda: _Connection(("oap_esim_requests", "oap_esim_events")),
    )

    status = esim_runtime.configure()

    assert status["persistence_attached"] is True
    assert status["schema_ready"] is True
    assert status["reason"] == "ready"
    assert esim_provisioning.CORE.repository is not None
