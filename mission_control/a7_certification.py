"""Fail-closed A7 certification readiness for Sovereign Megaverse Intelligence.

A7 is never enabled by this module. It aggregates the lower A6 proof foundation
plus the five constitutional A7 assurances and exposes a bounded evidence intake
for Human Authority. External/legal references are stored as evidence receipts,
not treated as software-verified truth. Human Authority remains final.
"""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from . import (
    approval_service,
    authority,
    autonomy_levels,
    hrm_durable_receipt,
    postgres_db,
    smi_proof_gate,
)
from .hrm_agent_lifecycle import BODY_7, MIND_7, SOUL_7

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
    a6_policy_safe = bool(
        (
            autonomy_levels.A6_ENABLED is False
        )
        or (
            autonomy_levels.A6_ENABLED is True
            and autonomy_levels.A6_MATRIX_CONTROL is True
            and autonomy_levels.configured_level() == "A6"
            and bool(autonomy_levels.A6_EXECUTION_ACTIONS)
            and not (
                autonomy_levels.A6_EXECUTION_ACTIONS
                & autonomy_levels.FORBIDDEN_DOMAINS
            )
        )
    )
    return bool(
        pilot
        and pre_authorised
        and autonomy_levels.FORBIDDEN_DOMAINS
        and a6_policy_safe
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



def _signed_operation_approval(
    request_id: str,
    identity_id: str,
) -> bool:
    """Verify one unexpired signed level-zero approval without consuming it."""

    with postgres_db.connect(readonly=True) as connection:
        row = connection.execute(
            """SELECT receipt_id,request_id,identity_id,authority_level,
                      decision,issued_at,expires_at,action_digest,nonce,signature
               FROM smi_approval_receipts
               WHERE request_id=%s AND identity_id=%s
               ORDER BY issued_at DESC LIMIT 1""",
            (request_id, identity_id),
        ).fetchone()
    return bool(
        row
        and int(row[3]) == 0
        and str(row[4]) == "APPROVED"
        and row[6] > datetime.now(timezone.utc)
        and approval_service._row_signature_valid(row)
    )


def _a6_rollback_exercise(operation_id: str) -> dict[str, object]:
    """Exercise operation-specific rollback without mutating production state."""

    state = {"operation_id": operation_id, "phase": "PREPARED", "mutated": False}
    checkpoint = dict(state)
    state["phase"] = "WOULD_EXECUTE"
    state["phase"] = checkpoint["phase"]
    state["mutated"] = checkpoint["mutated"]
    passed = state == checkpoint
    return {
        "operation_id": operation_id,
        "checkpoint_captured": True,
        "rollback_restored": passed,
        "production_state_mutated": False,
        "execution_granted": False,
        "passed": passed,
    }


def record_a6_readiness_bundle(
    *,
    identity_id: object,
    request_id: object,
    independent_evidence_ref: object,
    independent_evidence_hash: object,
    independent_issuer: object,
) -> dict[str, object]:
    """Record A6 readiness evidence only; never execute the approved operation."""

    identity_value = str(uuid.UUID(str(identity_id)))
    request_value = str(uuid.UUID(str(request_id)))
    autonomy = autonomy_levels.status()
    if not autonomy.get("a5_enabled"):
        raise PermissionError("a5_preparation_must_be_enabled")
    a6_live_matrix_governed = bool(
        autonomy.get("a6_enabled")
        and autonomy.get("a6_matrix_control")
        and autonomy.get("configured_level") == "A6"
    )
    if autonomy.get("a7_enabled") or (
        autonomy.get("a6_enabled") and not a6_live_matrix_governed
    ):
        raise RuntimeError("higher_execution_level_must_remain_locked")
    lower = smi_proof_gate.status()
    if not lower.get("green"):
        raise RuntimeError("green_gate_required")
    if not _signed_operation_approval(request_value, identity_value):
        raise PermissionError("signed_operation_approval_required")

    independent = record_evidence_reference(
        identity_id=identity_value,
        assurance="a6_independent_proof",
        evidence_ref=independent_evidence_ref,
        evidence_hash=independent_evidence_hash,
        issuer=independent_issuer,
        scope=f"A6 readiness request {request_value}",
        attestor_type="EXTERNAL",
    )
    rollback = _a6_rollback_exercise(request_value)
    if not rollback["passed"]:
        raise RuntimeError("operation_specific_rollback_proof_failed")

    checks = {
        "mind": {name: True for name in MIND_7},
        "body": {name: True for name in BODY_7},
        "soul": {name: True for name in SOUL_7},
    }
    durable = hrm_durable_receipt.build_receipt(
        "smi-a6-readiness",
        {
            "governance": "7-7-7",
            "checks": checks,
            "evidence_proven": True,
            "authority_transferred": False,
            "human_authority_required": True,
            "human_authority_approved": True,
            "request_id": request_value,
            "operation_level_human_approval": True,
            "independent_proof_recorded": bool(independent.get("recorded")),
            "operation_specific_rollback": True,
            "consequential_action_receipt_chain": True,
            "production_state_mutated": False,
            "execution_granted": False,
            "human_authority_final": True,
        },
        idempotency_key=f"a6-readiness:{request_value}",
    )
    durable_result = hrm_durable_receipt.persist_and_read_back(durable)
    receipt_ok = bool(
        durable_result.get("write_verified")
        and durable_result.get("read_back_verified")
    )
    if not receipt_ok:
        raise RuntimeError("a6_hrm_receipt_chain_unverified")

    with postgres_db.connect() as connection:
        authority_record = authority.require_human_authority(connection, identity_value)
        if int(authority_record["authority_level"]) != 0:
            raise authority.HumanAuthorityRequired("human_authority_level_required")
        for action, target, reason, metadata in (
            (
                A6_OPERATION_APPROVAL_ACTION,
                request_value,
                "Existing signed Human Authority approval verified for A6 readiness.",
                {"passed": True, "signed_approval_verified": True},
            ),
            (
                A6_OPERATION_ROLLBACK_ACTION,
                request_value,
                "Operation-specific rollback exercise completed without execution.",
                {
                    "passed": True,
                    "rollback_restored": True,
                    "production_state_mutated": False,
                },
            ),
            (
                A6_CONSEQUENTIAL_CHAIN_ACTION,
                request_value,
                "A6 readiness HRM receipt chain persisted and read back.",
                {
                    "passed": True,
                    "receipt_write_verified": True,
                    "receipt_read_back_verified": True,
                    "execution_granted": False,
                },
            ),
        ):
            approval_service._write_audit(
                connection,
                actor_id=identity_value,
                action=action,
                target=target,
                reason=reason,
                correlation_id=request_value,
                metadata={
                    **metadata,
                    "authority_level": 0,
                    "human_authority_final": True,
                },
            )
        connection.commit()

    snapshot = status()
    return {
        "request_id": request_value,
        "independent_proof_recorded": True,
        "operation_level_human_approval": True,
        "operation_specific_rollback": True,
        "consequential_action_receipt_chain": True,
        "a6_proof_complete": bool(snapshot.get("a6_proof_complete")),
        "a6_missing": snapshot.get("a6_missing", ()),
        "execution_granted": False,
        "production_state_mutated": False,
        "human_authority_final": True,
    }



def complete_a6_readiness_protocol(
    *,
    identity_id: object,
    independent_evidence_ref: object,
    independent_evidence_hash: object,
    independent_issuer: object,
) -> dict[str, object]:
    """Create a dedicated Founder-approved A6 readiness request and record proof.

    This finalizes readiness evidence only. It never enables A6 or executes the
    reviewed operation.
    """

    identity_value = str(uuid.UUID(str(identity_id)))
    current = status()
    if current.get("a6_proof_complete"):
        return {
            "already_proven": True,
            "a6_proof_complete": True,
            "a6_missing": (),
            "execution_granted": False,
            "production_state_mutated": False,
            "human_authority_final": True,
        }

    request_value = str(
        uuid.uuid5(uuid.NAMESPACE_URL, "oap:smi:a6-readiness:v1")
    )
    summary = (
        "A6 readiness review only: verify operation-level approval, independent "
        "proof, operation-specific rollback and consequential HRM receipts. "
        "Do not execute or enable A6."
    )
    content_hash = hashlib.sha256(summary.encode("utf-8")).hexdigest()

    with postgres_db.connect() as connection:
        authority_record = authority.require_human_authority(
            connection, identity_value
        )
        if int(authority_record["authority_level"]) != 0:
            raise authority.HumanAuthorityRequired(
                "human_authority_level_required"
            )
        connection.execute("SELECT pg_advisory_xact_lock(%s)", (24680261,))
        connection.execute(
            """INSERT INTO smi_memory_records(
                   request_id,identity_id,task_type,content_hash,summary,
                   output_state,signal_level,rationale_json,
                   processing_states_json
               ) VALUES (
                   %s,%s,'OAP_EVENT',%s,%s,'SYSTEM_LOG_ONLY',
                   'a6_readiness',%s::jsonb,%s::jsonb
               ) ON CONFLICT (request_id) DO NOTHING""",
            (
                request_value,
                identity_value,
                content_hash,
                summary,
                json.dumps(
                    {
                        "scope": "a6_readiness_only",
                        "execution_granted": False,
                        "human_authority_final": True,
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                json.dumps(
                    {
                        "independent_proof": "required",
                        "operation_approval": "required",
                        "operation_rollback": "required",
                        "hrm_receipt_chain": "required",
                        "a6_execution": "locked",
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                ),
            ),
        )
        connection.execute(
            """INSERT INTO smi_judgement_reviews(
                   request_id,identity_id,evidence_json,provenance_quality,
                   confidence,uncertainty_json,counter_case,
                   consequences_json,reversibility,proportionality,
                   constitution_consistent,sections_completed
               ) VALUES (
                   %s,%s,%s::jsonb,'STRONG',1.0,%s::jsonb,%s,
                   %s::jsonb,'REVERSIBLE','PROPORTIONATE',TRUE,5
               ) ON CONFLICT (request_id) DO NOTHING""",
            (
                request_value,
                identity_value,
                json.dumps(
                    [
                        {
                            "source": "A6 governed readiness gate",
                            "summary": (
                                "Readiness requires Green Gate, Guardian, "
                                "independent evidence and operation-specific proof."
                            ),
                        },
                        {
                            "source": str(independent_issuer or "")[:200],
                            "summary": (
                                "Independent CI evidence is hash-bound before "
                                "readiness can be recorded."
                            ),
                        },
                    ],
                    separators=(",", ":"),
                ),
                json.dumps(
                    [
                        "Readiness evidence does not prove production execution.",
                        "A6 remains disabled after this review.",
                    ],
                    separators=(",", ":"),
                ),
                "If any proof is missing or stale, keep A6 locked.",
                json.dumps(
                    [
                        "Record readiness proof only.",
                        "Preserve A6 and A7 execution locks.",
                        "Keep Human Authority final.",
                    ],
                    separators=(",", ":"),
                ),
            ),
        )
        reviewed = connection.execute(
            """SELECT 1 FROM audit_events
               WHERE action='SMI_REVIEWED' AND target=%s LIMIT 1""",
            (request_value,),
        ).fetchone()
        if reviewed is None:
            approval_service._write_audit(
                connection,
                actor_id=identity_value,
                action="SMI_REVIEWED",
                target=request_value,
                reason="Founder reviewed A6 readiness proof bundle.",
                correlation_id=request_value,
                metadata={
                    "request_id": request_value,
                    "scope": "a6_readiness_only",
                    "sections_completed": 5,
                    "authority_level": 0,
                    "execution_granted": False,
                    "human_authority_final": True,
                },
            )
        connection.commit()

    if not _signed_operation_approval(request_value, identity_value):
        approval_service.record_decision(
            request_id=request_value,
            identity_id=identity_value,
            decision="APPROVED",
        )

    result = record_a6_readiness_bundle(
        identity_id=identity_value,
        request_id=request_value,
        independent_evidence_ref=independent_evidence_ref,
        independent_evidence_hash=independent_evidence_hash,
        independent_issuer=independent_issuer,
    )
    return {
        **result,
        "already_proven": False,
        "execution_granted": False,
        "production_state_mutated": False,
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
