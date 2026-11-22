from __future__ import annotations

from mission_control import smi_auto_repair
from mission_control import views


def _status(*, worker: bool = True, schema: bool = True, dead: int = 0):
    return {
        "schema_ready": schema,
        "worker_fresh": worker,
        "ready": schema and worker,
        "queued": 0,
        "running": 1,
        "retry": 0,
        "dead_letter": dead,
        "migration": "0004_organism_runtime",
        "error": None,
    }


class _Store:
    def __init__(self):
        self.recovery_limit = None
        self.schedule_limit = None

    def recover_stale(self, *, limit):
        self.recovery_limit = limit
        return 2

    def tick_scheduler(self, *, limit):
        self.schedule_limit = limit
        return 1


def test_auto_repair_uses_existing_bounded_transactional_recovery():
    store = _Store()
    observations = [_status(), _status()]
    result = smi_auto_repair.repair_runtime(
        observe=lambda: observations.pop(0),
        store_factory=lambda: store,
    )
    assert result["state"] == "RECOVERY_APPLIED_PENDING_JOB_PROOF"
    assert result["recovered_stale_leases"] == 2
    assert result["enqueued_due_schedules"] == 1
    assert store.recovery_limit == 10
    assert store.schedule_limit == 5
    assert result["readback_available"] is True
    assert result["execution_performed"] is True
    assert result["production_green"] is False
    assert result["deployment_performed"] is False
    assert result["guardian_hrm_bypassed"] is False
    assert result["consequential_action"] is False
    assert result["independent_approval"] is False
    assert result["founder_final"] is True


def test_auto_repair_blocks_when_worker_or_schema_missing():
    for raw in (_status(schema=False), _status(worker=False), None, {}):
        def forbidden():
            raise AssertionError("must not mutate unverified runtime")
        result = smi_auto_repair.repair_runtime(
            observe=lambda raw=raw: raw,
            store_factory=forbidden,
        )
        assert result["state"] == "BLOCKED"
        assert result["execution_performed"] is False
        assert result["production_green"] is False


def test_auto_repair_never_retries_dead_letters_or_claims_full_green():
    store = _Store()
    result = smi_auto_repair.repair_runtime(
        observe=lambda: _status(dead=2),
        store_factory=lambda: store,
    )
    assert "dead_letter_requires_review" in result["remaining"]
    assert result["state"] == "RECOVERY_APPLIED_PENDING_JOB_PROOF"
    assert result["production_green"] is False


def test_auto_repair_returns_unknown_on_transaction_failure():
    class Broken:
        def recover_stale(self, *, limit):
            raise OSError("secret database error")
    result = smi_auto_repair.repair_runtime(
        observe=lambda: _status(),
        store_factory=lambda: Broken(),
    )
    assert result["state"] == "UNKNOWN"
    assert result["error"] == "runtime_repair_unavailable"
    assert "secret" not in str(result)
    assert result["production_green"] is False


def test_auto_repair_endpoint_requires_csrf_and_founder(anonymous_client, client, monkeypatch):
    path = "/mission/smi/auto-repair/run"
    unauthenticated = anonymous_client.post(path, json={})
    assert unauthenticated.status_code == 401
    without_csrf = client.post(path, json={})
    assert without_csrf.status_code == 403

    monkeypatch.setattr(views.web_security, "csrf_valid", lambda request: True)
    monkeypatch.setattr(
        views.smi_auto_repair,
        "repair_runtime",
        lambda: {"state": "BLOCKED", "production_green": False},
    )
    accepted = client.post(path, json={})
    assert accepted.status_code == 200
    assert accepted.headers["Cache-Control"] == "no-store"
    assert accepted.get_json()["production_green"] is False
    invalid = client.post(path, json={"command": "deploy"})
    assert invalid.status_code == 400


def test_canonical_auto_fix_ui_uses_authenticated_repair_route():
    from pathlib import Path

    template = Path("mission_control/templates/ollama_chat.html").read_text()
    script = Path("mission_control/static/smi_chat_final.js").read_text()
    assert "mission_control.smi_auto_repair_run" in template
    assert "cfg.autoRepairUrl" in script
    assert "Stale leases recovered" in script
    assert "Consequential execution: NOT PERFORMED" in script


def test_repair_readback_redacts_untrusted_error_text():
    store = _Store()
    raw = _status()
    raw["error"] = "secret=private_database_password"
    result = smi_auto_repair.repair_runtime(
        observe=lambda: raw,
        store_factory=lambda: store,
    )
    assert result["before"]["error"] == "runtime_status_unknown"
    assert result["after"]["error"] == "runtime_status_unknown"
    assert "secret=private_database_password" not in str(result)
    assert result["production_green"] is False
