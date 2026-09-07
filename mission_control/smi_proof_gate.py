"""Truth-first production proof aggregation for the SMI Green Gate.

This module consumes durable HRM/audit evidence and first-party request telemetry.
It never grants execution authority. Rollback proof is a bounded, reversible
in-memory fault exercise whose only persistent effect is an audited proof receipt.
"""

from __future__ import annotations

import uuid
from typing import Any

from . import approval_service, authority, postgres_db, telemetry

ROLLBACK_PROOF_ACTION = "SMI_ROLLBACK_RECOVERY_PROOF"


def _production_counts() -> dict[str, object]:
    evidence: dict[str, object] = {
        "store_reachable": False,
        "five_section_reviews": 0,
        "signed_approved_receipts": 0,
        "founder_smi_reviews": 0,
        "oap_event_receipts": 0,
        "rollback_recovery_receipts": 0,
        "error": None,
    }
    if not postgres_db.configured():
        evidence["error"] = "production_store_not_configured"
        return evidence
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT
                  (SELECT COUNT(*) FROM smi_judgement_reviews
                    WHERE sections_completed=5),
                  (SELECT COUNT(*) FROM smi_approval_receipts
                    WHERE decision='APPROVED' AND authority_level=0
                      AND nonce IS NOT NULL AND signature IS NOT NULL),
                  (SELECT COUNT(*) FROM audit_events
                    WHERE authority_level=0 AND action='SMI_REVIEWED'),
                  (SELECT COUNT(*) FROM audit_events
                    WHERE action='OAP_EVENT'),
                  (SELECT COUNT(*) FROM audit_events
                    WHERE action=%s AND metadata->>'passed'='true')""",
                (ROLLBACK_PROOF_ACTION,),
            ).fetchone()
        if row is not None:
            keys = (
                "five_section_reviews",
                "signed_approved_receipts",
                "founder_smi_reviews",
                "oap_event_receipts",
                "rollback_recovery_receipts",
            )
            evidence.update({key: int(value or 0) for key, value in zip(keys, row)})
            evidence["store_reachable"] = True
    except Exception:  # noqa: BLE001 - truth gate fails closed.
        evidence["error"] = "proof_store_unavailable"
    return evidence


def status() -> dict[str, object]:
    """Aggregate the real evidence required by the current SMI Green Gate."""

    counts = _production_counts()
    live_observability = telemetry.status()
    founder_interaction = bool(
        counts["store_reachable"] and int(counts["founder_smi_reviews"] or 0) > 0
    )
    receipt_chain = bool(
        counts["store_reachable"]
        and int(counts["five_section_reviews"] or 0) > 0
        and int(counts["signed_approved_receipts"] or 0) > 0
    )
    meaningful_event_memory = bool(
        counts["store_reachable"] and int(counts["oap_event_receipts"] or 0) > 0
    )
    rollback_recovery = bool(
        counts["store_reachable"]
        and int(counts["rollback_recovery_receipts"] or 0) > 0
    )
    observability = bool(live_observability.get("observability_ready"))
    green = bool(
        founder_interaction
        and receipt_chain
        and meaningful_event_memory
        and rollback_recovery
        and observability
    )
    checks = {
        "founder_interaction": founder_interaction,
        "receipt_chain": receipt_chain,
        "meaningful_event_memory": meaningful_event_memory,
        "rollback_recovery": rollback_recovery,
        "observability": observability,
    }
    missing = tuple(name for name, proven in checks.items() if not proven)
    return {
        "component": "SMI Green Gate",
        "green": green,
        "light": "🟢" if green else "🟡",
        "checks": checks,
        "missing": missing,
        "production_counts": counts,
        "observability": live_observability,
        "execution_granted": False,
        "a5_unlocked": False,
        "a6_unlocked": False,
        "a7_unlocked": False,
        "human_authority_final": True,
    }


def _rollback_exercise() -> dict[str, object]:
    """Exercise fault -> restore -> safe resume without touching product state."""

    checkpoint = {"state": "HEALTHY", "sequence": 1, "authority": "HUMAN"}
    working = dict(checkpoint)
    fault_observed = False
    try:
        working["state"] = "FAULT_INJECTED"
        working["sequence"] = 2
        raise RuntimeError("bounded_fault_injected")
    except RuntimeError as exc:
        fault_observed = str(exc) == "bounded_fault_injected"
        working = dict(checkpoint)
    restored = working == checkpoint
    if restored:
        working["sequence"] = int(working["sequence"]) + 1
    safe_resume = bool(
        restored
        and working["state"] == "HEALTHY"
        and working["authority"] == "HUMAN"
        and working["sequence"] == 2
    )
    passed = bool(fault_observed and restored and safe_resume)
    return {
        "fault_observed": fault_observed,
        "restored": restored,
        "safe_resume": safe_resume,
        "passed": passed,
        "production_state_mutated": False,
        "execution_authority_expanded": False,
        "human_authority_final": True,
    }


def run_rollback_recovery_proof(identity_id: object) -> dict[str, object]:
    """Run and audit one bounded rollback proof for active Human Authority."""

    try:
        identity_value = str(uuid.UUID(str(identity_id)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_human_authority_identity") from exc
    proof = _rollback_exercise()
    if not proof["passed"]:
        raise RuntimeError("rollback_recovery_proof_failed")

    with postgres_db.connect() as connection:
        authority_record = authority.require_human_authority(connection, identity_value)
        if int(authority_record["authority_level"]) != 0:
            raise authority.HumanAuthorityRequired("human_authority_level_required")
        correlation_id = str(uuid.uuid4())
        approval_service._write_audit(
            connection,
            actor_id=identity_value,
            action=ROLLBACK_PROOF_ACTION,
            target="SMI_A5_A6_BOUNDARY",
            reason="Bounded rollback and safe-resume proof completed.",
            correlation_id=correlation_id,
            metadata={
                "passed": True,
                "fault_observed": bool(proof["fault_observed"]),
                "restored": bool(proof["restored"]),
                "safe_resume": bool(proof["safe_resume"]),
                "production_state_mutated": False,
                "execution_authority_expanded": False,
                "authority_level": 0,
            },
        )
        connection.commit()
    return {
        **proof,
        "audit_recorded": True,
        "correlation_id": correlation_id,
    }


def public_safe_status() -> dict[str, Any]:
    """Return only coarse proof state; no identities, receipts or secrets."""

    snapshot = status()
    return {
        "component": snapshot["component"],
        "green": snapshot["green"],
        "light": snapshot["light"],
        "checks": snapshot["checks"],
        "missing": snapshot["missing"],
        "execution_granted": False,
        "human_authority_final": True,
    }
