from __future__ import annotations

import json

import app as app_module
from mission_control import rights_persistence


def test_rights_persistence_cli_commands_are_registered(client):
    commands = app_module.app.cli.commands
    assert "oap-rights-persistence-status" in commands
    assert "oap-rights-persistence-plan" in commands
    assert "oap-init-rights-persistence" in commands


def test_rights_persistence_plan_is_dry_run_only(client, monkeypatch):
    calls = []

    def fake_init_schema(*, dry_run=False, assume_yes=False):
        calls.append((dry_run, assume_yes))
        return {
            "dry_run": dry_run,
            "migration": "0020_rights_provenance_core_v1",
            "checksum": "a" * 64,
            "tables": 4,
        }

    monkeypatch.setattr(rights_persistence, "init_schema", fake_init_schema)
    result = app_module.app.test_cli_runner().invoke(
        args=["oap-rights-persistence-plan"]
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["dry_run"] is True
    assert calls == [(True, True)]


def test_rights_persistence_apply_requires_explicit_yes(client, monkeypatch):
    calls = []

    def fake_init_schema(*, dry_run=False, assume_yes=False):
        calls.append((dry_run, assume_yes))
        if not assume_yes:
            raise RuntimeError("Explicit human approval required: pass --yes")
        return {"schema_ready": True}

    monkeypatch.setattr(rights_persistence, "init_schema", fake_init_schema)

    blocked = app_module.app.test_cli_runner().invoke(
        args=["oap-init-rights-persistence"]
    )
    assert blocked.exit_code != 0
    assert calls == [(False, False)]

    allowed = app_module.app.test_cli_runner().invoke(
        args=["oap-init-rights-persistence", "--yes"]
    )
    assert allowed.exit_code == 0
    assert json.loads(allowed.output)["schema_ready"] is True
    assert calls[-1] == (False, True)


def test_rights_persistence_status_is_read_only(client, monkeypatch):
    monkeypatch.setattr(
        rights_persistence,
        "schema_status",
        lambda: {
            "schema_ready": False,
            "error": "rights_persistence_schema_pending",
        },
    )
    result = app_module.app.test_cli_runner().invoke(
        args=["oap-rights-persistence-status"]
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema_ready"] is False
    assert payload["error"] == "rights_persistence_schema_pending"
