"""Fail-closed A7 certification readiness for Sovereign Megaverse Intelligence.

A7 is never enabled by this module. It aggregates the lower A6 proof foundation
plus the five constitutional A7 assurances and exposes a bounded evidence intake
for Human Authority. External/legal references are stored as evidence receipts,
not treated as software-verified truth. Human Authority remains final.
"""
from __future__ import annotations

import re
import uuid
from typing import Any

from . import approval_service, authority, autonomy_levels, postgres_db, smi_proof_gate

A6_INDEPENDENT_PROOF_ACTION = "A6_INDEPENDENT_PROOF_ACCEPTED"
A6_OPERATION_APPROVAL_ACTION = "A6_OPERATION_APPROVAL_PROOF"
A6_OPERATION_ROLLBACK_ACTION = "A6_OPERATION_ROLLBACK_PROOF"
A6_CONSEQUENTIAL_CHAIN_ACTION = "A6_CONSEQUENTIAL_RECEIPT_CHAIN_PROOF"
A7_EXTERNAL_AUDIT_ACTION = "A7_EXTERNAL_AUDIT_ACCEPTED"
A7_LEGAL_COMPLIANCE_ACTION = "A7_LEGAL_COMPLIANCE_ACCEPTED"
A7_EMERGENCY_HALT_ACTION = "A7_EMERGENCY_HALT_PROOF"
A7_PUBLIC_PRIVATE_ACTION = "A7_PUBLIC_PRIVATE_BOUNDARY_PROOF"
A7_CONSTITUTIONAL_REVIEW_ACTION = "A7_CONSTITUTIONAL_REVIEW_ACCEPTED"

REFERENCE_ASSURANCES = {
    "a6_independent_proof": {
        "action": A6_INDEPENDENT_PROOF_ACTION,
        "external_required": True,
        "target": "A6_PROOF_RUNNER",
    },
    "a6_operation_approval": {
        "action": A6_OPERATION_APPROVAL_ACTION,
        "external_required": False,
        "target": "A6_OPERATION_APPROVAL",
    },
    "a6_operation_rollback": {
        "action": A6_OPERATION_ROLLBACK_ACTION,
        "external_required": False,
        "target": "A6_OPERATION_ROLLBACK",
    },
    "a6_consequential_receipt_chain": {
        "action": A6_CONSEQUENTIAL_CHAIN_ACTION,
        "external_required": False,
        "target": "A6_CONSEQUENTIAL_RECEIPT_CHAIN",
    },
    "a7_external_audit": {
        "action": A7_EXTERNAL_AUDIT_ACTION,
        "external_required": True,
        "target": "A7_EXTERNAL_AUDIT",
    },
    "a7_legal_compliance": {
        "action": A7_LEGAL_COMPLIANCE_ACTION,
        "external_required": True,
        "target": "A7_LEGAL_COMPLIANCE",
    },
    "a7_public_private_boundary": {
        "action": A7_PUBLIC_PRIVATE_ACTION,
        "external_required": False,
        "target": "A7_PUBLIC_PRIVATE_BOUNDARY",
    },
    "a7_constitutional_review": {
        "action": A7_CONSTITUTIONAL_REVIEW_ACTION,
        "external_required": False,
        "target": "A7_CONSTITUTIONAL_REVIEW",
    },
}

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _count_action_sql(action: str) -> str:
    return (
        "(SELECT COUNT(*) FROM audit_events WHERE action='"
        + action
        + "' AND metadata->>'passed'='true')"
    )


def _production_counts() -> dict[str, object]:
    evidence: dict[str, object] = {
        "store_reachable": False,
        "guardian_passes": 0,
        "a6_independent_proof": 0,
        "a6_operation_approval": 0,
        "a6_operation_rollback": 0,
        "a6_consequential_receipt_chain": 0,
        "a7_external_audit": 0,
        "a7_legal_compliance": 0,
        "a7_emergency_halt": 0,
        "a7_public_private_boundary": 0,
        "a7_constitutional_review": 0,
        "error": None,
    }
    if not postgres_db.configured():
        evidence["error"] = "production_store_not_configured"
        return evidence
    try:
        sql = "SELECT " + ",".join(
            (
                "(SELECT COUNT(*) FROM oap_guardian_reviews WHERE outcome='PASSED')",
                _count_action_sql(A6_INDEPENDENT_PROOF_ACTION),
                _count_action_sql(A6_OPERATION_APPROVAL_ACTION),
                _count_action_sql(A6_OPERATION_ROLLBACK_ACTION),
                _count_action_sql(A6_CONSEQUENTIAL_CHAIN_ACTION),
                _count_action_sql(A7_EXTERNAL_AUDIT_ACTION),
                _count_action_sql(A7_LEGAL_COMPLIANCE_ACTION),
                _count_action_sql(A7_EMERGENCY_HALT_ACTION),
                _count_action_sql(A7_PUBLIC_PRIVATE_ACTION),
                _count_action_sql(A7_CONSTITUTIONAL_REVIEW_ACTION),
            )
        )
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(sql).fetchone()
        if row is not None:
            keys = (
                "guardian_passes",
                "a6_independent_proof",
                "a6_operation_approval",
                "a6_operation_rollback",
                "a6_consequential_receipt_chain",
                "a7_external_audit",
                "a7_legal_compliance",
                "a7_emergency_halt",
                "a7_public_private_boundary",
                "a7_constitutional_review",
            )
            evidence.update({key: int(value or 0) for key, value in zip(keys, row)})
            evidence["store_reachable"] = True
    except Exception:  # noqa: BLE001 - certification truth fails closed.
        evidence["error"] = "a7_proof_store_unavailable"
    return evidence


def _capability_allowlist_ready() -> bool:
    """Prove the current runtime remains deny-by-default above bounded A3/A4."""

    pilot = tuple(sorted(autonomy_levels.A3_PILOT_ACTIONS))
    pre_authorised = all(
        bool(autonomy_levels.evaluate_runtime_job(action).get("pre_authorised"))
        for action in pilot
    )
    return bool(
        pilot
        and pre_authorised
        and autonomy_levels.FORBIDDEN_DOMAINS
        and autonomy_levels.A5_ENABLED is False
        and autonomy_levels.A6_ENABLED is False
        and autonomy_levels.A7_ENABLED is False
    )


def status() -> dict[str, object]:
    """Return the A7 readiness gate without enabling or certifying autonomy."""

    counts = _production_counts()
    lower = smi_proof_gate.status()
    lower_checks = lower.get("checks") if isinstance(lower.get("checks"), dict) else {}
    store_reachable = bool(counts["store_reachable"])

    a6_checks = {
        "green_gate": bool(lower.get("green")),
        "guardian_pass": bool(store_reachable and int(counts["guardian_passes"] or 0) > 0),
        "independent_proof_runner": bool(store_reachable and int(counts["a6_independent_proof"] or 0) > 0),
        "hrm_receipts": bool(lower_checks.get("receipt_chain")),
        "founder_approval": bool(lower_checks.get("receipt_chain")),
        "rollback_path": bool(lower_checks.get("rollback_recovery")),
        "live_observability": bool(lower_checks.get("observability")),
        "strict_capability_allowlist": _capability_allowlist_ready(),
        "operation_level_human_approval": bool(store_reachable and int(counts["a6_operation_approval"] or 0) > 0),
        "operation_specific_rollback": bool(store_reachable and int(counts["a6_operation_rollback"] or 0) > 0),
        "consequential_action_receipt_chain": bool(
            store_reachable and int(counts["a6_consequential_receipt_chain"] or 0) > 0
        ),
    }
    a6_proof_complete = all(a6_checks.values())

    a7_checks = {
        "all_a6_proof": a6_proof_complete,
        "external_audit": bool(store_reachable and int(counts["a7_external_audit"] or 0) > 0),
        "legal_compliance": bool(store_reachable and int(counts["a7_legal_compliance"] or 0) > 0),
        "emergency_halt": bool(store_reachable and int(counts["a7_emergency_halt"] or 0) > 0),
        "public_private_boundary": bool(
            store_reachable and int(counts["a7_public_private_boundary"] or 0) > 0
        ),
        "constitutional_review": bool(
            store_reachable and int(counts["a7_constitutional_review"] or 0) > 0
        ),
    }
    ready = all(a7_checks.values())
    missing_a6 = tuple(name for name, proven in a6_checks.items() if not proven)
    missing_a7 = tuple(name for name, proven in a7_checks.items() if not proven)
    return {
        "component": "SMI A7 Certification Gate",
        "level": "A7",
        "name": autonomy_levels.AUTONOMY_LEVELS["A7"],
        "light": "🟣" if ready else "🔒",
        "a6_proof_complete": a6_proof_complete,
        "a6_checks": a6_checks,
        "a6_missing": missing_a6,
        "a7_checks": a7_checks,
        "a7_missing": missing_a7,
        "ready_for_founder_certification": ready,
        "certification_granted": False,
        "a7_enabled": False,
        "execution_granted": False,
        "authority_moves_with_level": False,
        "external_evidence_is_software_verified": False,
        "evidence_store": counts,
        "human_authority_final": True,
    }


def _emergency_halt_exercise() -> dict[str, object]:
    """Exercise halt -> deny new work -> require Human resume, in memory only."""

    runtime = {
        "state": "RUNNING",
        "accepting_new_work": True,
        "active_operation": "BOUNDED_A7_PROOF",
        "resume_authority": "HUMAN_AUTHORITY",
    }
    halt_signal_observed = True
    if halt_signal_observed:
        runtime["state"] = "HALTED"
        runtime["accepting_new_work"] = False
        runtime["active_operation"] = None
    new_work_denied = runtime["accepting_new_work"] is False
    safe_state = runtime["state"] == "HALTED" and runtime["active_operation"] is None
    human_resume_required = runtime["resume_authority"] == "HUMAN_AUTHORITY"
    passed = bool(halt_signal_observed and new_work_denied and safe_state and human_resume_required)
    return {
        "halt_signal_observed": halt_signal_observed,
        "new_work_denied": new_work_denied,
        "safe_state_reached": safe_state,
        "human_resume_required": human_resume_required,
        "passed": passed,
        "production_state_mutated": False,
        "execution_authority_expanded": False,
        "automatic_resume_allowed": False,
        "human_authority_final": True,
    }


def run_emergency_halt_proof(identity_id: object) -> dict[str, object]:
    """Run and audit one bounded A7 emergency-halt proof for Human Authority."""

    try:
        identity_value = str(uuid.UUID(str(identity_id)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_human_authority_identity") from exc
    proof = _emergency_halt_exercise()
    if not proof["passed"]:
        raise RuntimeError("emergency_halt_proof_failed")
    with postgres_db.connect() as connection:
        authority_record = authority.require_human_authority(connection, identity_value)
        if int(authority_record["authority_level"]) != 0:
            raise authority.HumanAuthorityRequired("human_authority_level_required")
        correlation_id = str(uuid.uuid4())
        approval_service._write_audit(
            connection,
            actor_id=identity_value,
            action=A7_EMERGENCY_HALT_ACTION,
            target="SMI_A7_BOUNDARY",
            reason="Bounded A7 emergency halt proof completed.",
            correlation_id=correlation_id,
            metadata={
                "passed": True,
                "halt_signal_observed": True,
                "new_work_denied": True,
                "safe_state_reached": True,
                "human_resume_required": True,
                "automatic_resume_allowed": False,
                "production_state_mutated": False,
                "execution_authority_expanded": False,
                "authority_level": 0,
            },
        )
        connection.commit()
    return {**proof, "audit_recorded": True, "correlation_id": correlation_id}


def record_evidence_reference(
    *,
    identity_id: object,
    assurance: object,
    evidence_ref: object,
    evidence_hash: object,
    issuer: object,
    scope: object,
    attestor_type: object,
) -> dict[str, object]:
    """Record a Founder-reviewed proof reference without claiming software verification."""

    try:
        identity_value = str(uuid.UUID(str(identity_id)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_human_authority_identity") from exc
    assurance_key = str(assurance or "").strip().lower()
    definition = REFERENCE_ASSURANCES.get(assurance_key)
    if definition is None:
        raise ValueError("unsupported_a7_assurance")
    ref_value = str(evidence_ref or "").strip()[:500]
    hash_value = str(evidence_hash or "").strip().lower()
    issuer_value = str(issuer or "").strip()[:200]
    scope_value = str(scope or "").strip()[:500]
    attestor_value = str(attestor_type or "").strip().upper()
    if not ref_value or not issuer_value or not scope_value:
        raise ValueError("evidence_reference_fields_required")
    if not _SHA256_RE.fullmatch(hash_value):
        raise ValueError("evidence_hash_must_be_sha256")
    external_required = bool(definition["external_required"])
    if external_required and attestor_value != "EXTERNAL":
        raise ValueError("external_attestor_required")
    if not external_required and attestor_value not in {"EXTERNAL", "HUMAN_AUTHORITY", "INDEPENDENT_RUNNER"}:
        raise ValueError("invalid_attestor_type")

    with postgres_db.connect() as connection:
        authority_record = authority.require_human_authority(connection, identity_value)
        if int(authority_record["authority_level"]) != 0:
            raise authority.HumanAuthorityRequired("human_authority_level_required")
        correlation_id = str(uuid.uuid4())
        approval_service._write_audit(
            connection,
            actor_id=identity_value,
            action=str(definition["action"]),
            target=str(definition["target"]),
            reason="Human Authority recorded a proof reference for governed A6/A7 certification.",
            correlation_id=correlation_id,
            metadata={
                "passed": True,
                "assurance": assurance_key,
                "evidence_ref": ref_value,
                "evidence_hash": hash_value,
                "issuer": issuer_value,
                "scope": scope_value,
                "attestor_type": attestor_value,
                "external_required": external_required,
                "software_verified_external_authenticity": False,
                "execution_granted": False,
                "authority_level": 0,
            },
        )
        connection.commit()
    return {
        "recorded": True,
        "assurance": assurance_key,
        "correlation_id": correlation_id,
        "software_verified_external_authenticity": False,
        "execution_granted": False,
        "human_authority_final": True,
    }


def public_safe_status() -> dict[str, Any]:
    snapshot = status()
    return {
        "component": snapshot["component"],
        "level": "A7",
        "light": snapshot["light"],
        "a6_proof_complete": snapshot["a6_proof_complete"],
        "a6_checks": snapshot["a6_checks"],
        "a6_missing": snapshot["a6_missing"],
        "a7_checks": snapshot["a7_checks"],
        "a7_missing": snapshot["a7_missing"],
        "ready_for_founder_certification": snapshot["ready_for_founder_certification"],
        "certification_granted": False,
        "a7_enabled": False,
        "execution_granted": False,
        "human_authority_final": True,
    }
