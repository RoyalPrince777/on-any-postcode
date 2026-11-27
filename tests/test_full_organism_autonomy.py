from __future__ import annotations

from mission_control import organism, organism_autonomy, organism_worker
from mission_control.organism_runtime import RuntimeJob


def _job(kind: str) -> RuntimeJob:
    return RuntimeJob(
        job_id="00000000-0000-0000-0000-000000000258",
        job_type=kind,
        payload={},
        attempts=1,
        max_attempts=5,
        idempotency_key="full-organism-autonomy-test",
    )


def test_full_anatomy_contains_oap_owned_organs_and_single_brain():
    validation = organism.validate_architecture()
    systems = {item["id"]: item for item in organism.ORGANISM_SYSTEMS}
    organs = {item["id"]: item for item in organism.BODY_ORGANS}

    assert validation["passed"] is True
    assert validation["checks"]["brain_count"] == 1
    assert systems["smi"]["anatomy"] == "Brain"
    assert systems["oap_core"]["name"] == "OAP CORE"
    assert systems["nexus"]["anatomy"] == "Nervous system"
    assert systems["living_kernel"]["anatomy"] == "Heart"
    assert organs["tune_core"]["name"] == "OAP Music"
    assert organs["commerce_core"]["name"] == "OAP Commerce Core"
    assert organs["post_core"]["name"] == "OAP Post Core"
    assert organs["movement"]["anatomy"] == "Locomotor system"
    assert validation["checks"]["body_organs"] == len(organism.BODY_ORGANS)


def test_signal_path_keeps_human_authority_before_execution():
    path = organism.ORGANISM_SIGNAL_PATH

    assert path[:5] == (
        "OAP CORE",
        "NEXUS",
        "Thalamus",
        "SMI Brain",
        "Judgement",
    )
    assert path.index("Human Authority") < path.index("Living Kernel")
    assert path.index("Living Kernel") < path.index("Body Organ")
    assert path[-1] == "HRM"


def test_every_body_organ_has_bounded_autonomy_and_human_authority():
    safe = set(organism.SAFE_AUTONOMY_ACTIONS)
    blocked = set(organism.BLOCKED_CONSEQUENTIAL_ACTIONS)

    assert "self_apply_improvement" in blocked
    assert "deploy" in blocked
    assert "payment_capture" in blocked
    assert "driver_dispatch" in blocked
    assert "production_migration" in blocked
    for organ in organism.BODY_ORGANS:
        assert set(organ["safe_autonomy"]) <= safe
        assert set(organ["gated_edges"]) <= blocked
        assert organ["human_authority_final"] is True


def test_organism_autonomy_policy_never_grants_final_authority():
    state = organism_autonomy.status()

    assert state["mode"] == "BOUNDED_AUTONOMOUS"
    assert state["configured"] is True
    assert state["automatic_observation"] is True
    assert state["automatic_cross_organ_coherence"] is True
    assert state["automatic_recovery_review"] is True
    assert state["automatic_growth_proposals"] is True
    assert state["independent_approval"] is False
    assert state["independent_execution"] is False
    assert state["independent_apply"] is False
    assert state["human_authority_final"] is True


def test_full_cycle_detects_missing_runtime_and_product_readiness(monkeypatch):
    monkeypatch.setattr(
        organism_autonomy,
        "runtime_status",
        lambda: {"schema_ready": True, "worker_fresh": False},
    )
    monkeypatch.setattr(
        organism_autonomy.product_cores,
        "product_core_schema_status",
        lambda: {"schema_ready": False},
    )
    monkeypatch.setattr(
        organism_autonomy,
        "movement_schema_status",
        lambda: {"schema_ready": True},
    )
    monkeypatch.setattr(
        organism_autonomy.routing,
        "status",
        lambda: {"production_ready": False},
    )

    cycle = organism_autonomy.run_cycle()

    assert cycle["consequential_action"] is False
    assert cycle["independent_approval"] is False
    assert cycle["independent_execution"] is False
    assert cycle["independent_apply"] is False
    assert cycle["human_authority_final"] is True
    assert "runtime_worker_not_fresh" in cycle["coherence"]["issues"]
    assert "product_cores_not_ready" in cycle["coherence"]["issues"]
    assert "routing_not_production_ready" in cycle["coherence"]["issues"]
    assert cycle["recovery"]["destructive_recovery_allowed"] is False
    assert cycle["growth"]["requires_human_approval"] is True
    assert cycle["growth"]["sandbox_required"] is True
    assert cycle["growth"]["reversibility_required"] is True


def test_worker_heartbeat_carries_whole_organism_autonomy():
    result = organism_worker._heartbeat_job(_job("RUNTIME_HEARTBEAT"))

    assert result["consequential_action"] is False
    assert result["organism_autonomy"]["mode"] == "BOUNDED_AUTONOMOUS"
    assert result["organism_autonomy"]["human_authority_final"] is True


def test_full_physiology_has_complete_non_authoritative_body_model():
    anatomy = organism.get_public_anatomy()
    physiology = {item["id"]: item for item in anatomy["physiology_systems"]}

    expected = {
        "dna",
        "genes",
        "blood",
        "circulation",
        "lungs",
        "skin",
        "digestive",
        "liver_kidneys",
        "metabolism",
        "energy",
        "endocrine",
        "immune",
        "healing",
        "muscles",
        "cells",
        "growth",
    }
    assert set(physiology) == expected
    assert anatomy["validation"]["checks"]["physiology_systems"] == len(expected)
    assert physiology["dna"]["can_execute"] is False
    assert physiology["blood"]["can_execute"] is False
    assert physiology["circulation"]["can_execute"] is False
    assert physiology["immune"]["can_execute"] is False
    assert physiology["muscles"]["can_execute"] is True
    assert physiology["growth"]["can_execute"] is False


def test_physiology_flow_keeps_authority_before_action_and_learning_after_outcome():
    flow = organism.ORGANISM_PHYSIOLOGY_FLOW

    assert flow.index("Human Authority") < flow.index("Living Kernel / Heart")
    assert flow.index("Living Kernel / Heart") < flow.index("Muscles + Body Organs")
    assert flow.index("Muscles + Body Organs") < flow.index("Outcome sensors")
    assert flow.index("Outcome sensors") < flow.index("HRM Memory")
    assert flow.index("HRM Memory") < flow.index("Matrix Learning")
    assert flow.index("Matrix Learning") < flow.index("Growth proposal")


def test_physiology_laws_preserve_single_brain_and_human_authority():
    joined = " ".join(organism.PHYSIOLOGY_LAWS)

    assert "Human Authority remains final" in joined
    assert "SMI interprets" in joined
    assert "NEXUS circulates signals" in joined
    assert "Growth proposes reversible improvements" in joined


def test_organism_page_renders_full_physiology(client):
    response = client.get("/mission/organism")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "DNA · Blood · Organs · Recovery · Growth" in page
    assert "OAP DNA" in page
    assert "OAP Blood" in page
    assert "OAP Lungs" in page
    assert "OAP Immune System" in page
    assert "OAP Healing System" in page
    assert "OAP Muscles" in page


def test_native_cycle_accounts_for_canonical_physiology_without_certifying_organs():
    evidence = organism_autonomy.physiology_evidence(
        {"architecture_ready": True, "runtime_job_receipt_verified": False},
        {"proposed_actions": ("review:runtime",)},
    )
    systems = evidence["systems"]
    assert set(systems) == {system["id"] for system in organism.PHYSIOLOGY_SYSTEMS}
    assert systems["dna"]["check_observed"] is True
    assert systems["cells"]["check_observed"] is False
    assert systems["growth"]["check_observed"] is True
    assert systems["immune"]["check_observed"] is False
    assert systems["muscles"]["check_observed"] is False
    assert all(item["operational_status"] == "Unknown" for item in systems.values())
    assert evidence["full_organism_verified"] is False


def test_native_health_cycle_carries_physiology_evidence(monkeypatch):
    monkeypatch.setattr(organism_worker.postgres_db, "postgres_status",
                        lambda: {"initialized": False})
    monkeypatch.delenv("OAP_SMI_GITHUB_READ_TOKEN", raising=False)
    result = organism_worker._health_probe(_job("RUNTIME_HEALTH_PROBE"))
    evidence = result["organism_autonomy"]["physiology_evidence"]
    assert set(evidence["systems"]) == {
        system["id"] for system in organism.PHYSIOLOGY_SYSTEMS
    }
    assert evidence["full_organism_verified"] is False
    assert result["consequential_action"] is False


def test_native_anatomy_uses_actual_health_checks_without_inheriting_green():
    cycle = {
        "observation": {"oap_core_autonomy_ready": True},
        "physiology_evidence": organism_autonomy.physiology_evidence({}, {}),
    }
    evidence = organism_autonomy.native_anatomy_evidence(cycle, {
        "health_checks": {"nexus": True, "thalamus_input": True,
                          "agent_registry": True, "guardian": True},
    })
    assert set(evidence["systems"]) == {item["id"] for item in organism.ORGANISM_SYSTEMS}
    assert set(evidence["brain_regions"]) == {item["id"] for item in organism.SMI_REGIONS}
    assert set(evidence["body_organs"]) == {item["id"] for item in organism.BODY_ORGANS}
    assert evidence["systems"]["nexus"]["observed"] is True
    assert evidence["systems"]["smi"]["observed"] is False
    assert evidence["systems"]["sp_signals"]["observed"] is False
    physiology = cycle["physiology_evidence"]["systems"]
    assert physiology["circulation"]["check_observed"] is True
    assert physiology["genes"]["check_observed"] is True
    assert physiology["immune"]["check_observed"] is False
    assert all(item["operational_status"] == "Unknown" for item in physiology.values())
    assert evidence["full_organism_verified"] is False


def test_coherence_requires_verified_durable_receipt():
    observation = {
        "architecture_ready": True,
        "runtime_schema_ready": True,
        "runtime_worker_fresh": True,
        "product_cores_ready": True,
        "movement_ready": True,
        "routing_production_ready": True,
        "oap_core_autonomy_ready": True,
        "smi_autonomy_ready": True,
        "body_organs": organism.BODY_ORGANS,
    }
    for value in (None, False, 1, "true"):
        review = organism_autonomy.coherence_review(
            {**observation, "runtime_job_receipt_verified": value}
        )
        assert review["coherent"] is False
        assert review["issues"] == ("runtime_job_receipt_unverified",)
        assert organism_autonomy.recovery_review(review)["recovery_attention"] is True
        assert "review:runtime_job_receipt_unverified" in organism_autonomy.growth_proposal(review)["proposed_actions"]
    missing = organism_autonomy.coherence_review(observation)
    assert missing["coherent"] is False
    assert missing["issues"] == ("runtime_job_receipt_unverified",)
    verified = organism_autonomy.coherence_review(
        {**observation, "runtime_job_receipt_verified": True}
    )
    assert verified["coherent"] is True
    assert verified["issues"] == ()
    assert verified["review_only"] is True
    assert verified["consequential_action"] is False


def test_empty_coherence_observation_fails_closed(monkeypatch):
    def unexpected_observe():
        raise AssertionError("Explicit empty evidence must not be replaced")

    monkeypatch.setattr(organism_autonomy, "observe", unexpected_observe)
    review = organism_autonomy.coherence_review({})
    assert review["coherent"] is False
    assert "runtime_job_receipt_unverified" in review["issues"]
