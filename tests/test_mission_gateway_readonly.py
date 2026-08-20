from __future__ import annotations

import hashlib
import sqlite3

import app as app_module
from mission_control import config, status


def test_mission_renders_without_initializing_database(client, tmp_path):
    database_path = tmp_path / "uninitialized-oap.db"
    assert not database_path.exists()

    response = client.get("/mission")

    assert response.status_code == 200
    assert "Mission Control database not initialized" in response.get_data(as_text=True)
    assert not database_path.exists()


def test_invalid_mode_returns_structured_400(client):
    response = client.get("/mission?mode=execute")

    assert response.status_code == 400
    assert response.get_json() == {
        "error": {
            "allowed_modes": ["sovereign", "mission", "approval"],
            "code": "invalid_mode",
            "message": "Unsupported Mission Control mode.",
        }
    }


def test_public_status_is_coarse_and_redacted(client):
    response = client.get("/mission/status")

    assert response.status_code == 200
    payload = response.get_json()
    serialized = response.get_data(as_text=True).lower()
    assert payload["human_authority"]["status"] == "Final approval required"
    assert len(payload["agents"]) == 6
    for private_key in (
        "actor_id",
        "approval_target",
        "correlation_id",
        "private_message",
        "prompt",
        "totp",
        "secret",
    ):
        assert private_key not in serialized


def test_privileged_status_fails_closed_without_authentication(client):
    response = client.get("/mission/status?scope=authorized")

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "authentication_required"


def test_authorized_status_service_fails_closed():
    try:
        status.get_authorized_mission_status({"authenticated": True})
    except PermissionError as exc:
        assert "Identity and Permission checks" in str(exc)
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("Privileged status must remain unavailable")


def test_status_get_does_not_change_existing_database(client, tmp_path, monkeypatch):
    database_path = tmp_path / "legacy.db"
    connection = sqlite3.connect(database_path)
    connection.execute("CREATE TABLE legacy_records (id INTEGER PRIMARY KEY, note TEXT)")
    connection.execute("INSERT INTO legacy_records(note) VALUES ('preserve me')")
    connection.commit()
    connection.close()

    before = hashlib.sha256(database_path.read_bytes()).hexdigest()
    monkeypatch.setattr(config, "OAP_DATABASE_PATH", str(database_path))

    response = client.get("/mission/status")

    after = hashlib.sha256(database_path.read_bytes()).hexdigest()
    assert response.status_code == 200
    assert before == after
    connection = sqlite3.connect(f"file:{database_path.resolve()}?mode=ro", uri=True)
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    connection.close()
    assert tables == {"legacy_records"}
    assert not database_path.with_name(database_path.name + "-wal").exists()


def test_public_timeline_uses_allowlist_and_omits_private_fields(
    client, tmp_path, monkeypatch
):
    database_path = tmp_path / "initialized.db"
    connection = sqlite3.connect(database_path)
    connection.execute(
        "CREATE TABLE schema_migrations ("
        "version TEXT PRIMARY KEY, name TEXT, checksum TEXT, applied_at TEXT)"
    )
    connection.execute(
        "INSERT INTO schema_migrations VALUES "
        "('0001_audit_foundation', '0001_audit_foundation.py', 'test', 'now')"
    )
    connection.execute(
        "CREATE TABLE audit_events ("
        "event_seq INTEGER PRIMARY KEY, action TEXT, timestamp TEXT, "
        "actor_id TEXT, target TEXT, correlation_id TEXT)"
    )
    connection.execute(
        "INSERT INTO audit_events VALUES "
        "(1, 'HUMAN_APPROVED', '2026-08-17T08:00:00Z', "
        "'private-actor', 'private-target', 'private-correlation')"
    )
    connection.execute(
        "INSERT INTO audit_events VALUES "
        "(2, 'PRIVATE_ACTION', '2026-08-17T08:01:00Z', "
        "'private-actor', 'private-target', 'private-correlation')"
    )
    connection.commit()
    connection.close()
    monkeypatch.setattr(config, "OAP_DATABASE_PATH", str(database_path))

    response = client.get("/mission/status")
    serialized = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Human approval recorded" in serialized
    assert "PRIVATE_ACTION" not in serialized
    assert "private-actor" not in serialized
    assert "private-target" not in serialized
    assert "private-correlation" not in serialized


def test_mission_routes_register_get_only(client):
    rules = {
        rule.rule: set(rule.methods or ())
        for rule in app_module.app.url_map.iter_rules()
        if rule.rule.startswith("/mission")
    }

    assert rules["/mission"] == {"GET", "HEAD", "OPTIONS"}
    assert rules["/mission/"] == {"GET", "HEAD", "OPTIONS"}
    assert rules["/mission/organism"] == {"GET", "HEAD", "OPTIONS"}
    assert rules["/mission/status"] == {"GET", "HEAD", "OPTIONS"}
    assert "/mission/chat" not in rules
    assert "/mission/order" not in rules
