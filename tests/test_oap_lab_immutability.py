"""Read-only proof tests for LAB database immutability readiness."""
from mission_control import workspaces


class _Result:
    def __init__(self, row):
        self._row = row

    def fetchone(self):
        return self._row


class _Connection:
    def __init__(self, *, update_allowed, delete_allowed, trigger):
        self.update_allowed = update_allowed
        self.delete_allowed = delete_allowed
        self.trigger = trigger
        self.readonly = False

    def execute(self, sql, params=None):
        if "has_table_privilege" in sql:
            return _Result((self.update_allowed, self.delete_allowed))
        if "FROM pg_trigger" in sql:
            return _Result((1,) if self.trigger else None)
        raise AssertionError(sql)


class _Context:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self.connection

    def __exit__(self, exc_type, exc, tb):
        return False


def test_lab_immutability_green_when_app_role_cannot_update_or_delete(monkeypatch):
    connection = _Connection(
        update_allowed=False, delete_allowed=False, trigger=False,
    )

    def connect(*, readonly=False):
        assert readonly is True
        return _Context(connection)

    monkeypatch.setattr(workspaces.postgres_db, "lab_connect", connect)
    result = workspaces.lab_immutability_status()
    assert result["database_enforced"] is True
    assert result["update_denied"] is True
    assert result["delete_denied"] is True
    assert result["schema_changed"] is False


def test_lab_immutability_green_with_enabled_protective_trigger(monkeypatch):
    connection = _Connection(
        update_allowed=True, delete_allowed=True, trigger=True,
    )
    monkeypatch.setattr(
        workspaces.postgres_db,
        "lab_connect",
        lambda *, readonly=False: _Context(connection),
    )
    result = workspaces.lab_immutability_status()
    assert result["database_enforced"] is True
    assert result["protective_trigger_present"] is True


def test_lab_immutability_fails_closed_when_rows_are_mutable(monkeypatch):
    connection = _Connection(
        update_allowed=True, delete_allowed=True, trigger=False,
    )
    monkeypatch.setattr(
        workspaces.postgres_db,
        "lab_connect",
        lambda *, readonly=False: _Context(connection),
    )
    result = workspaces.lab_immutability_status()
    assert result["database_enforced"] is False


def test_lab_immutability_probe_failure_never_claims_green(monkeypatch):
    def connect(*, readonly=False):
        raise RuntimeError("offline")

    monkeypatch.setattr(workspaces.postgres_db, "lab_connect", connect)
    result = workspaces.lab_immutability_status()
    assert result["database_enforced"] is False
    assert result["error"] == "workspace_immutability_probe_failed"
