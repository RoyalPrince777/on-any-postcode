"""Live-releasable Mail tooling must not expose an operational DDL command."""
from __future__ import annotations

import json

import app as app_module
from mission_control import mail_migration, mail_preflight, postgres_db


def test_mail_operational_commands_expose_only_readonly_scope(client):
    commands = app_module.app.cli.commands
    for name in (
        "oap-mail-preflight", "oap-mail-status", "oap-mail-migration-plan",
    ):
        assert name in commands
    assert "oap-init-mail" not in commands
    assert not any(
        command.startswith("oap-mail") and "apply" in command
        for command in commands
    )


def test_mail_preflight_cli_is_redacted_and_never_writes(client, monkeypatch):
    calls = []

    def forbidden_connect(*_args, **_kwargs):
        calls.append("connect")
        raise AssertionError("preflight must not write")
    monkeypatch.setattr(postgres_db, "connect", forbidden_connect)
    monkeypatch.setattr(mail_preflight, "report", lambda: {
        "read_only": True, "recovery_point_verified": False,
        "live_migration_authorized": False,
    })
    result = app_module.app.test_cli_runner().invoke(args=["oap-mail-preflight"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["read_only"] is True
    assert payload["recovery_point_verified"] is False
    assert payload["live_migration_authorized"] is False
    assert calls == []


def test_mail_migration_plan_does_not_connect_or_apply_schema(client, monkeypatch):
    calls = []

    def forbidden_connect(*_args, **_kwargs):
        calls.append("connect")
        raise AssertionError("Mail migration plan touched database")
    monkeypatch.setattr(postgres_db, "connect", forbidden_connect)
    monkeypatch.setattr(postgres_db, "postgres_status",
                        lambda: calls.append("status"))
    result = app_module.app.test_cli_runner().invoke(
        args=["oap-mail-migration-plan"],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["dry_run"] is True
    assert payload["applied"] is False
    assert payload["statements"] == 2
    assert len(payload["checksum"]) == 64
    assert calls == []


def test_mail_schema_status_command_does_not_pretend_migration(client, monkeypatch):
    calls = []
    monkeypatch.setattr(mail_migration, "schema_status", lambda: {
        "schema_ready": False, "error": "mail_migration_pending",
    })
    monkeypatch.setattr(postgres_db, "connect",
                        lambda **_kw: calls.append("connect"))
    result = app_module.app.test_cli_runner().invoke(args=["oap-mail-status"])
    assert result.exit_code == 0
    assert json.loads(result.output)["schema_ready"] is False
    assert calls == []
