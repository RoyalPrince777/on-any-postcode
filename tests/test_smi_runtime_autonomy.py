from __future__ import annotations

from mission_control import organism_worker, smi_runtime_autonomy


def _health(*, approval_receipt: bool = False):
    checks = {
        "database": True,
        "schema": True,
        "provider_key": True,
        "provider_assignment": True,
        "identity": True,
        "permission": True,
        "nexus": True,
        "thalamus_input": True,
        "agent_registry": True,
        "biological_brain": True,
        "aegis": True,
        "guardian": True,
        "war_room": True,
        "hrm": True,
        "conversation_memory": True,
        "judgement_five_sections": True,
        "router": True,
        "chat_route": True,
        "audit": True,
        "human_authority": True,
        "approval_receipt": approval_receipt,
    }
    return {
        "status": "green" if all(checks.values()) else "degraded",
        "checks": checks,
        "green": sum(checks.values()),
        "total": len(checks),
        "invariants": {
            "execution_locked": True,
            "human_authority_final": True,
        },
    }


def test_smi_runtime_cycle_uses_21_gate_evidence_without_execution(monkeypatch):
    monkeypatch.setattr(smi_runtime_autonomy.smi_chat_runtime, "health", _health)

    cycle = smi_runtime_autonomy.run_cycle()

    assert cycle["kind"] == "smi_autonomy_cycle"
    assert cycle["mode"] == "BOUNDED_AUTONOMOUS"
    assert cycle["source"] == "production_3x7_21_gate_health"
    assert cycle["gates_green"] == 20
    assert cycle["gates_total"] == 21
    assert cycle["health_status"] == "degraded"
    assert cycle["production_invariants"] == {
        "execution_locked": True,
        "human_authority_final": True,
    }
    assert cycle["provider_completion_performed"] is False
    assert cycle["hrm_record_created"] is False
    assert cycle["independent_approval"] is False
    assert cycle["independent_execution"] is False
    assert cycle["independent_apply"] is False
    assert cycle["human_authority_final"] is True
    assert cycle["consequential_action"] is False
    assert cycle["controlled_self_improvement_runtime"]["ready"] is False


def test_smi_runtime_improvement_gate_requires_real_governance_evidence(monkeypatch):
    monkeypatch.setattr(
        smi_runtime_autonomy.smi_chat_runtime,
        "health",
        lambda: _health(approval_receipt=True),
    )

    cycle = smi_runtime_autonomy.run_cycle()

    assert cycle["gates_green"] == 21
    assert cycle["health_status"] == "green"
    assert cycle["controlled_self_improvement_runtime"]["ready"] is True
    assert cycle["controlled_self_improvement_runtime"]["human_approval_required"] is True
    assert cycle["controlled_self_improvement_runtime"]["living_kernel_required"] is True
    assert cycle["controlled_self_improvement_runtime"]["independent_apply"] is False


def test_smi_runtime_status_does_not_probe_health(monkeypatch):
    def forbidden():
        raise AssertionError("status must not run production health probe")

    monkeypatch.setattr(smi_runtime_autonomy.smi_chat_runtime, "health", forbidden)

    state = smi_runtime_autonomy.status()

    assert state["configured"] is True
    assert state["health_probe_on_status"] is False
    assert state["provider_completion_performed"] is False
    assert state["hrm_record_created"] is False
    assert state["consequential_action"] is False


def test_worker_health_probe_runs_all_three_autonomy_layers(monkeypatch):
    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, query):
            del query
            return self

        def fetchone(self):
            return (1,)

    monkeypatch.setattr(
        organism_worker.postgres_db,
        "postgres_status",
        lambda: {"initialized": True},
    )
    monkeypatch.setattr(
        organism_worker.postgres_db,
        "connect",
        lambda readonly=False: Connection(),
    )
    monkeypatch.setattr(
        organism_worker.oap_core_autonomy,
        "run_cycle",
        lambda: {"kind": "oap_core", "consequential_action": False},
    )
    monkeypatch.setattr(
        organism_worker.smi_runtime_autonomy,
        "run_cycle",
        lambda: {"kind": "smi", "consequential_action": False},
    )
    monkeypatch.setattr(
        organism_worker.organism_autonomy,
        "run_cycle",
        lambda: {"kind": "organism", "consequential_action": False},
    )

    result = organism_worker._health_probe(object())

    assert result["human_authority_present"] is True
    assert result["oap_core_autonomy"]["kind"] == "oap_core"
    assert result["smi_autonomy"]["kind"] == "smi"
    assert result["organism_autonomy"]["kind"] == "organism"
    assert result["human_authority_final"] is True
    assert result["independent_execution"] is False
    assert result["consequential_action"] is False


def test_worker_heartbeat_exposes_all_three_autonomy_boundaries(monkeypatch):
    monkeypatch.setattr(
        organism_worker.oap_core_autonomy,
        "status",
        lambda: {"configured": True},
    )
    monkeypatch.setattr(
        organism_worker.smi_runtime_autonomy,
        "status",
        lambda: {"configured": True},
    )
    monkeypatch.setattr(
        organism_worker.organism_autonomy,
        "status",
        lambda: {"configured": True},
    )

    heartbeat = organism_worker._heartbeat_job(object())

    assert heartbeat["oap_core_autonomy"]["configured"] is True
    assert heartbeat["smi_autonomy"]["configured"] is True
    assert heartbeat["organism_autonomy"]["configured"] is True
    assert heartbeat["human_authority_final"] is True
    assert heartbeat["independent_execution"] is False
    assert heartbeat["consequential_action"] is False
