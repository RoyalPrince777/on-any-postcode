from __future__ import annotations

from pathlib import Path

from mission_control import smi_recursive_improvement


def _smi_cycle(*, improvement_ready: bool = False):
    return {
        "gates_green": 20,
        "gates_total": 21,
        "proposal": {"evidence": ("degraded:conversation_memory",)},
        "controlled_self_improvement_runtime": {"ready": improvement_ready},
        "consequential_action": False,
    }


def _core_cycle(*, worker_fresh: bool = False):
    return {
        "observation": {"runtime_worker_fresh": worker_fresh},
        "coherence": {"issues": ("runtime_worker_not_fresh",)},
        "consequential_action": False,
    }


def _organism_cycle():
    return {
        "coherence": {"issues": ("routing_not_production_ready",)},
        "consequential_action": False,
    }


def _completion():
    return {
        "runtime_evidence": {"store_reachable": True},
        "missing_proof_gates": (
            {"id": "hrm_receipt_chain", "proven": False},
        ),
        "consequential_action": False,
    }


def test_recursive_cycle_prepares_deterministic_reversible_candidate(monkeypatch):
    monkeypatch.setenv("RENDER_GIT_COMMIT", "a" * 40)
    monkeypatch.setattr(smi_recursive_improvement.smi_runtime_autonomy, "run_cycle", _smi_cycle)
    monkeypatch.setattr(smi_recursive_improvement.oap_core_autonomy, "run_cycle", _core_cycle)
    monkeypatch.setattr(smi_recursive_improvement.organism_autonomy, "run_cycle", _organism_cycle)
    monkeypatch.setattr(
        smi_recursive_improvement.smi_completion_contract,
        "completion_status",
        _completion,
    )

    first = smi_recursive_improvement.run_cycle()
    second = smi_recursive_improvement.run_cycle()

    assert first["kind"] == "smi_governed_recursive_improvement_cycle"
    assert first["output_state"] == "REVIEW_REQUIRED"
    assert first["light"] == "orange"
    assert first["candidate"]["candidate_id"] == second["candidate"]["candidate_id"]
    assert first["candidate"]["reversible"] is True
    assert first["candidate"]["sandbox_passed"] is False
    assert first["candidate"]["promotion_ready"] is False
    assert first["proof"]["signed_approval_recorded"] is False
    assert first["proof"]["promotion_executed"] is False
    assert first["proof"]["hrm_record_created_by_this_view"] is False
    assert first["independent_approval"] is False
    assert first["independent_execution"] is False
    assert first["independent_apply"] is False
    assert first["consequential_action"] is False
    assert "self_deploy" in first["hard_locks"]


def test_recursive_cycle_fails_closed_when_an_evidence_layer_errors(monkeypatch):
    def unavailable():
        raise RuntimeError("secret detail must not escape")

    monkeypatch.setattr(smi_recursive_improvement.smi_runtime_autonomy, "run_cycle", unavailable)
    monkeypatch.setattr(smi_recursive_improvement.oap_core_autonomy, "run_cycle", _core_cycle)
    monkeypatch.setattr(smi_recursive_improvement.organism_autonomy, "run_cycle", _organism_cycle)
    monkeypatch.setattr(
        smi_recursive_improvement.smi_completion_contract,
        "completion_status",
        _completion,
    )

    cycle = smi_recursive_improvement.run_cycle()

    assert "unknown:smi_evidence" in cycle["weaknesses"]
    assert cycle["output_state"] == "REVIEW_REQUIRED"
    assert "secret detail" not in str(cycle)


def test_recursive_improvement_routes_render_live_evidence_and_no_store(
    client, monkeypatch
):
    cycle = {
        "light": "orange",
        "output_state": "REVIEW_REQUIRED",
        "recommendation": "Review evidence.",
        "weaknesses": ("proof_required:hrm_receipt_chain",),
        "proof": {
            "smi_gates_green": 20,
            "smi_gates_total": 21,
            "continuous_cycle_proven": False,
            "production_store_reachable": True,
            "governance_evidence_ready": False,
        },
        "candidate": {
            "candidate_id": "rsi-test",
            "baseline_version": "test",
            "evidence_digest": "a" * 64,
        },
        "loop": smi_recursive_improvement.LOOP_STAGES,
        "hard_locks": smi_recursive_improvement.HARD_LOCKS,
    }
    monkeypatch.setattr(smi_recursive_improvement, "run_cycle", lambda: cycle)

    page = client.get("/mission/improvement")
    api = client.get("/mission/improvement/status")
    assert page.status_code == 200
    assert "Improvement Loop" in page.get_data(as_text=True)
    assert page.headers["Cache-Control"] == "no-store"
    assert api.status_code == 200
    assert api.get_json()["output_state"] == "REVIEW_REQUIRED"
    assert api.headers["Cache-Control"] == "no-store"


def test_recursive_improvement_routes_fail_closed_anonymously(anonymous_client):
    anonymous_page = anonymous_client.get("/mission/improvement")
    anonymous_api = anonymous_client.get("/mission/improvement/status")

    assert anonymous_page.status_code == 302
    assert "/enter-my-world?next=" in anonymous_page.headers["Location"]
    assert anonymous_api.status_code == 401
    assert anonymous_api.get_json()["error"]["code"] == "authentication_required"


def test_personal_smi_and_mission_control_link_the_improvement_loop():
    mission = Path("mission_control/templates/mission.html").read_text(encoding="utf-8")
    chat = Path("mission_control/templates/ollama_chat.html").read_text(encoding="utf-8")
    controller = Path("mission_control/static/smi_chat_final.js").read_text(encoding="utf-8")

    assert "mission_control.smi_recursive_improvement_dashboard" in mission
    assert "Improvement Loop" in mission
    assert "improvementUrl" in chat
    assert "Improvement Loop" in controller
