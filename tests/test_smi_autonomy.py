from __future__ import annotations

import sqlite3

from oap.audit import initialize_audit_schema
from oap.contracts import IdentityRecord
from oap.hrm import initialize_brain_schema
from oap.smi.bootstrap import build_smi


def _brain():
    connection = sqlite3.connect(":memory:")
    initialize_audit_schema(connection)
    initialize_brain_schema(connection)
    human = IdentityRecord(
        identity_id="founder-1",
        identity_type="human_authority",
        authority_level=0,
        permissions=frozenset({"REQUEST_RECOMMENDATION", "APPROVE_RECOMMENDATION"}),
        roles=("human_authority",),
    )
    return build_smi(connection, identities=(human,))


def test_smi_status_exposes_bounded_autonomy_without_execution_authority():
    brain = _brain()
    status = brain.status()

    assert status["bounded_autonomous"] is True
    assert status["independent_execute"] is False
    assert status["independent_approval"] is False
    assert status["independent_apply"] is False
    assert status["human_authority_final"] is True
    assert status["autonomy"]["mode"] == "BOUNDED_AUTONOMOUS"
    assert status["autonomy"]["consequential_action"] is False


def test_smi_autonomy_cycle_observes_and_proposes_without_recording_a_request():
    brain = _brain()
    before = brain.hrm.status()["memory_records"]

    cycle = brain.autonomy_cycle()

    assert cycle["kind"] == "smi_autonomy_cycle"
    assert cycle["observation"]["read_only"] is True
    assert cycle["observation"]["sentience_claimed"] is False
    assert cycle["observation"]["consciousness_claimed"] is False
    assert cycle["coherence"]["review_only"] is True
    assert cycle["recovery"]["destructive_recovery_allowed"] is False
    assert cycle["recovery"]["authority_change_allowed"] is False
    assert cycle["proposal"]["requires_human_approval"] is True
    assert cycle["proposal"]["sandbox_required"] is True
    assert cycle["proposal"]["reversibility_required"] is True
    assert cycle["proposal"]["independent_apply"] is False
    assert cycle["independent_approval"] is False
    assert cycle["independent_execution"] is False
    assert cycle["consequential_action"] is False
    assert brain.hrm.status()["memory_records"] == before


def test_smi_autonomy_policy_blocks_consequential_and_self_promoting_actions():
    brain = _brain()
    policy = brain.autonomy.status()
    blocked = set(policy["blocked_actions"])

    assert {
        "approve_recommendation",
        "self_promote",
        "self_apply_improvement",
        "deploy",
        "payment_capture",
        "driver_dispatch",
        "permission_change",
        "production_migration",
        "esim_activation",
        "public_precise_tracking",
    } <= blocked
    assert policy["human_authority_final"] is True
    assert policy["independent_execution"] is False


def test_smi_autonomy_degraded_state_generates_review_not_execution():
    brain = _brain()
    cycle = brain.autonomy.run_cycle(
        components=(
            {"component": "A", "ready": True},
            {"component": "B", "ready": False},
        ),
        self_model={
            "overall_ready": False,
            "degraded_components": ("B",),
            "unknown_components": (),
        },
        coherence={
            "coherent": True,
            "checked_components": 2,
            "uncertainty": 0.0,
            "human_review_required": False,
            "conflicts": (),
        },
        evolution={"ready": True},
    )

    assert cycle["recovery"]["recovery_attention"] is True
    assert "review:degraded:B" in cycle["proposal"]["proposed_actions"]
    assert cycle["proposal"]["requires_human_approval"] is True
    assert cycle["consequential_action"] is False
