from mission_control import runtime_state_binding


class _Cursor:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None


class _Connection:
    def __init__(self, tables, fks):
        self.tables = set(tables)
        self.fks = set(fks)

    def execute(self, query, params=None):
        if "information_schema.tables" in query:
            return _Cursor([(name,) for name in sorted(self.tables)])
        if "constraint_type='FOREIGN KEY'" in query:
            return _Cursor([(1,)] if tuple(params or ()) in self.fks else [])
        raise AssertionError(query)


class _Context:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self.connection

    def __exit__(self, exc_type, exc, tb):
        return False


def test_probe_proves_only_observed_read_only_bindings(monkeypatch):
    tables = {
        "users",
        "oap_workspace_records",
        "oap_arena_matches",
        "oap_arena_player_profiles",
    }
    fks = {
        ("oap_workspace_records", "identity_id", "users"),
        ("oap_arena_player_profiles", "identity_id", "users"),
        ("oap_arena_matches", "player_a_id", "users"),
        ("oap_arena_matches", "player_b_id", "users"),
    }
    monkeypatch.setattr(
        runtime_state_binding.postgres_db,
        "database_identity_fingerprint",
        lambda: {
            "source": "platform_database_url",
            "authority": "primary",
            "reachable": True,
            "fingerprint": "a" * 32,
        },
    )
    monkeypatch.setattr(
        runtime_state_binding.postgres_db,
        "connect",
        lambda readonly=False: _Context(_Connection(tables, fks)),
    )

    status = runtime_state_binding.probe()

    assert status["read_only"] is True
    assert status["schema_changed"] is False
    assert status["domains"]["identity"]["state"] == "SCHEMA_PROVEN"
    assert status["domains"]["arena_profile"]["state"] == "SCHEMA_PROVEN"
    assert status["domains"]["arena_competition"]["state"] == "SCHEMA_PROVEN"
    assert status["domains"]["organiser"]["state"] == "SCHEMA_PROVEN"
    assert status["domains"]["studio"]["state"] == "SCHEMA_PROVEN"
    assert status["domains"]["value"]["state"] == "UNPROVEN"
    assert status["all_canonical_domains_schema_proven"] is False


def test_probe_fails_closed_when_database_unreachable(monkeypatch):
    monkeypatch.setattr(
        runtime_state_binding.postgres_db,
        "database_identity_fingerprint",
        lambda: {
            "source": "unconfigured",
            "authority": "primary",
            "reachable": False,
            "fingerprint": None,
        },
    )

    status = runtime_state_binding.probe()

    assert status["proven_count"] == 0
    assert status["all_canonical_domains_schema_proven"] is False
    assert status["error"] == "canonical_database_unreachable"
