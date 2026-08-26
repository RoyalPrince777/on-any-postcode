from __future__ import annotations

from mission_control import oap_core_autonomy, organism_worker
from mission_control.organism_runtime import RuntimeJob


def _job(kind: str) -> RuntimeJob:
    return RuntimeJob(
        job_id="00000000-0000-0000-0000-000000000009",
        job_type=kind,
        payload={},
        attempts=1,
        max_attempts=5,
        idempotency_key="autonomy-test",
    )


def test_oap_core_autonomy_policy_never_grants_execution_authority():
    state = oap_core_autonomy.status()

    assert state["mode"] == "BOUNDED_AUTONOMOUS"
    assert state["configured"] is True
    assert state["automatic_observation"] is True
    assert state["automatic_coherence_review"] is True
    assert state["automatic_recovery_review"] is True
    assert state["automatic_improvement_proposals"] is True
    assert state["independent_execution"] is False
    assert state["independent_apply"] is False
    assert state["human_authority_final"] is True
    assert "deploy" in state["blocked_actions"]
    assert "payment_capture" in state["blocked_actions"]
    assert "driver_dispatch" in state["blocked_actions"]
    assert "production_migration" in state["blocked_actions"]
    assert "self_apply_improvement" in state["blocked_actions"]


def test_autonomous_cycle_observes_reviews_and_proposes_without_acting(monkeypatch):
    monkeypatch.setattr(
        oap_core_autonomy.postgres_db,
        "postgres_status",
        lambda: {"initialized": True},
    )
    monkeypatch.setattr(
        oap_core_autonomy,
        "runtime_status",
        lambda: {
            "ready": True,
            "schema_ready": True,
            "worker_fresh": True,
            "retry": 2,
            "dead_letter": 1,
        },
    )
    monkeypatch.setattr(
        oap_core_autonomy,
        "movement_schema_status",
        lambda: {"schema_ready": True},
    )
    monkeypatch.setattr(
        oap_core_autonomy,
        "product_core_schema_status",
        lambda: {"schema_ready": True},
    )
    monkeypatch.setattr(
        oap_core_autonomy.routing,
        "status",
        lambda: {
            "provider_tier": "production_candidate",
            "production_ready": False,
        },
    )

    cycle = oap_core_autonomy.run_cycle()

    assert cycle["consequential_action"] is False
    assert cycle["independent_execution"] is False
    assert cycle["human_authority_final"] is True
    assert cycle["observation"]["retry_jobs"] == 2
    assert cycle["recovery"]["recovery_attention"] is True
    assert cycle["recovery"]["destructive_recovery_allowed"] is False
    assert "runtime_dead_letters_present" in cycle["coherence"]["issues"]
    assert "routing_candidate_not_promoted" in cycle["coherence"]["issues"]
    assert "product_core_schema_not_ready" not in cycle["coherence"]["issues"]
    assert cycle["proposal"]["requires_human_approval"] is True
    assert cycle["proposal"]["sandbox_required"] is True
    assert cycle["proposal"]["reversibility_required"] is True
    assert cycle["proposal"]["independent_apply"] is False


def test_product_core_schema_drift_is_visible_to_oap_core(monkeypatch):
    monkeypatch.setattr(
        oap_core_autonomy,
        "runtime_status",
        lambda: {"schema_ready": True, "worker_fresh": True, "dead_letter": 0},
    )
    monkeypatch.setattr(
        oap_core_autonomy,
        "movement_schema_status",
        lambda: {"schema_ready": True},
    )
    monkeypatch.setattr(
        oap_core_autonomy,
        "product_core_schema_status",
        lambda: {"schema_ready": False},
    )
    monkeypatch.setattr(
        oap_core_autonomy.routing,
        "status",
        lambda: {"provider_tier": "demo", "production_ready": False},
    )

    review = oap_core_autonomy.coherence_review()

    assert review["coherent"] is False
    assert "product_core_schema_not_ready" in review["issues"]


def test_runtime_heartbeat_carries_autonomy_policy_without_executing():
    result = organism_worker._heartbeat_job(_job("RUNTIME_HEARTBEAT"))

    assert result["consequential_action"] is False
    assert result["oap_core_autonomy"]["mode"] == "BOUNDED_AUTONOMOUS"
    assert result["oap_core_autonomy"]["independent_execution"] is False


def test_health_probe_runs_one_bounded_autonomy_cycle(monkeypatch):
    monkeypatch.setattr(
        organism_worker.postgres_db,
        "postgres_status",
        lambda: {"initialized": False},
    )
    monkeypatch.setattr(
        organism_worker.oap_core_autonomy,
        "run_cycle",
        lambda: {
            "kind": "oap_core_autonomy_cycle",
            "human_authority_final": True,
            "independent_execution": False,
            "consequential_action": False,
        },
    )

    result = organism_worker._health_probe(_job("RUNTIME_HEALTH_PROBE"))

    assert result["database_ready"] is False
    assert result["human_authority_present"] is False
    assert result["consequential_action"] is False
    assert result["oap_core_autonomy"]["independent_execution"] is False
    assert result["oap_core_autonomy"]["human_authority_final"] is True