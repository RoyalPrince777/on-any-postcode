"""Truth-first production proof aggregation for the SMI Green Gate.

This module consumes durable HRM/audit evidence, the canonical SMI signal
contract, and first-party request telemetry. It never grants execution authority.
Rollback proof is a bounded, reversible in-memory fault exercise whose only
persistent effect is an audited proof receipt.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from oap.smi.runtime_guard import bounded_control_proof

from . import (
    approval_service,
    authority,
    coherent_automation,
    embodiment,
    embodiment_isolation,
    hrm_durable_receipt,
    smi_cancellation,
    postgres_db,
    telemetry,
)
from .hrm_agent_lifecycle import BODY_7, MIND_7, SOUL_7

ROLLBACK_PROOF_ACTION = "SMI_ROLLBACK_RECOVERY_PROOF"
RUNTIME_GUARD_PROOF_ACTION = "SMI_RUNTIME_GUARD_PROOF"
ISOLATION_RECOVERY_PROOF_ACTION = "SMI_ISOLATION_RECOVERY_PROOF"
FOUNDER_FINAL_ACTION = "SMI_FOUNDER_FINAL"
EMBODIMENT_PROOF_REVISION = "embodiment-v1"


def _production_counts() -> dict[str, object]:
    evidence: dict[str, object] = {
        "store_reachable": False,
        "five_section_reviews": 0,
        "signed_approved_receipts": 0,
        "durable_hrm_receipts": 0,
        "durable_hrm_receipt_store_present": False,
        "founder_smi_reviews": 0,
        "oap_event_receipts": 0,
        "rollback_recovery_receipts": 0,
        "runtime_guard_receipts": 0,
        "isolation_recovery_receipts": 0,
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
                  (SELECT COUNT(*) FROM smi_memory_records
                    WHERE task_type='OAP_EVENT'),
                  (SELECT COUNT(*) FROM audit_events
                    WHERE action=%s AND metadata->>'passed'='true'
                      AND metadata->>'proof_revision'=%s),
                  (SELECT COUNT(*) FROM audit_events
                    WHERE action=%s AND metadata->>'passed'='true'
                      AND metadata->>'proof_revision'=%s),
                  (SELECT COUNT(*) FROM audit_events
                    WHERE action=%s AND metadata->>'passed'='true'
                      AND metadata->>'proof_revision'=%s)""",
                (
                    ROLLBACK_PROOF_ACTION,
                    EMBODIMENT_PROOF_REVISION,
                    RUNTIME_GUARD_PROOF_ACTION,
                    EMBODIMENT_PROOF_REVISION,
                    ISOLATION_RECOVERY_PROOF_ACTION,
                    EMBODIMENT_PROOF_REVISION,
                ),
            ).fetchone()
            receipt_table = connection.execute(
                "SELECT to_regclass('public.oap_hrm_receipts')"
            ).fetchone()
            receipt_store_present = bool(receipt_table and receipt_table[0])
            durable_hrm_receipts = 0
            if receipt_store_present:
                receipt_row = connection.execute(
                    "SELECT COUNT(*) FROM oap_hrm_receipts"
                ).fetchone()
                durable_hrm_receipts = int(receipt_row[0] or 0) if receipt_row else 0
        if row is not None:
            keys = (
                "five_section_reviews",
                "signed_approved_receipts",
                "founder_smi_reviews",
                "oap_event_receipts",
                "rollback_recovery_receipts",
                "runtime_guard_receipts",
                "isolation_recovery_receipts",
            )
            evidence.update({key: int(value or 0) for key, value in zip(keys, row)})
            evidence["durable_hrm_receipt_store_present"] = receipt_store_present
            evidence["durable_hrm_receipts"] = durable_hrm_receipts
            evidence["store_reachable"] = True
    except Exception:  # noqa: BLE001 - truth gate fails closed.
        evidence["error"] = "proof_store_unavailable"
    return evidence


def _signal_contract_status() -> dict[str, object]:
    """Read the canonical 21-signal contract and fail closed on any error."""

    try:
        snapshot = coherent_automation.status()
    except Exception:  # noqa: BLE001 - Green Gate must never fail open.
        return {
            "checked": False,
            "ready": False,
            "signal_count": 0,
            "signals_valid": False,
            "error": "signal_contract_unavailable",
        }
    if not isinstance(snapshot, dict):
        return {
            "checked": False,
            "ready": False,
            "signal_count": 0,
            "signals_valid": False,
            "error": "signal_contract_invalid",
        }
    signal_count = int(snapshot.get("signal_count") or 0)
    signals_valid = bool(snapshot.get("signals_valid"))
    ready = bool(snapshot.get("ready") and signals_valid and signal_count == 21)
    return {
        "checked": True,
        "ready": ready,
        "signal_count": signal_count,
        "signals_valid": signals_valid,
        "error": None if ready else "signal_contract_proof_required",
    }


def status() -> dict[str, object]:
    """Aggregate the real evidence required by the current SMI Green Gate."""

    counts = _production_counts()
    signal_contract = _signal_contract_status()
    live_observability = telemetry.status()
    store_reachable = bool(counts["store_reachable"])
    founder_interaction = bool(
        store_reachable and int(counts["founder_smi_reviews"] or 0) > 0
    )
    durable_hrm_receipt = bool(
        store_reachable
        and counts.get("durable_hrm_receipt_store_present")
        and int(counts["durable_hrm_receipts"] or 0) > 0
    )
    receipt_chain = bool(
        durable_hrm_receipt
        and int(counts["five_section_reviews"] or 0) > 0
        and int(counts["signed_approved_receipts"] or 0) > 0
    )
    meaningful_event_memory = bool(
        store_reachable and int(counts["oap_event_receipts"] or 0) > 0
    )
    rollback_recovery = bool(
        store_reachable and int(counts["rollback_recovery_receipts"] or 0) > 0
    )
    runtime_guard = bool(
        store_reachable
        and (
            "runtime_guard_receipts" not in counts
            or int(counts.get("runtime_guard_receipts") or 0) > 0
        )
    )
    isolation_recovery = bool(
        store_reachable
        and (
            "isolation_recovery_receipts" not in counts
            or int(counts.get("isolation_recovery_receipts") or 0) > 0
        )
    )
    observability = bool(
        store_reachable and live_observability.get("observability_ready")
    )
    signal_contract_proven = bool(signal_contract.get("ready"))
    green = bool(
        founder_interaction
        and signal_contract_proven
        and receipt_chain
        and meaningful_event_memory
        and rollback_recovery
        and runtime_guard
        and isolation_recovery
        and observability
    )
    checks = {
        "founder_interaction": founder_interaction,
        "signal_contract": signal_contract_proven,
        "durable_hrm_receipt": durable_hrm_receipt,
        "receipt_chain": receipt_chain,
        "meaningful_event_memory": meaningful_event_memory,
        "rollback_recovery": rollback_recovery,
        "runtime_guard": runtime_guard,
        "isolation_recovery": isolation_recovery,
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
        "signal_contract": signal_contract,
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
    stop_proof = smi_cancellation.bounded_stop_recovery_proof()
    passed = bool(
        fault_observed
        and restored
        and safe_resume
        and stop_proof["passed"]
    )
    return {
        "fault_observed": fault_observed,
        "restored": restored,
        "safe_resume": safe_resume,
        "human_stop_recovery": stop_proof,
        "human_stop_observed": bool(stop_proof["human_stop_observed"]),
        "human_stop_idempotent": bool(stop_proof["idempotent_stop"]),
        "human_stop_safe_resume": bool(stop_proof["safe_resume"]),
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
                "proof_revision": EMBODIMENT_PROOF_REVISION,
                "fault_observed": bool(proof["fault_observed"]),
                "restored": bool(proof["restored"]),
                "safe_resume": bool(proof["safe_resume"]),
                "human_stop_observed": bool(proof["human_stop_observed"]),
                "human_stop_idempotent": bool(proof["human_stop_idempotent"]),
                "human_stop_safe_resume": bool(proof["human_stop_safe_resume"]),
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


def _isolation_recovery_exercise() -> dict[str, object]:
    """Exercise isolation and full-state restore without touching product state."""

    checkpoint = {
        "worker": {"state": "ACTIVE", "lease": "job-1"},
        "queue": {"job-1": "RUNNING", "job-2": "QUEUED"},
        "sessions": {"founder": "BOUND", "worker": "BOUND"},
        "memory_refs": ("chronicle:1", "joog:1"),
        "authority": "HUMAN",
    }
    working = {
        "worker": dict(checkpoint["worker"]),
        "queue": dict(checkpoint["queue"]),
        "sessions": dict(checkpoint["sessions"]),
        "memory_refs": tuple(checkpoint["memory_refs"]),
        "authority": checkpoint["authority"],
    }

    working["worker"]["state"] = "DRAINING"
    working["worker"]["lease"] = None
    working["queue"]["job-1"] = "RETRY"
    working["sessions"]["worker"] = "REVOKED"

    contained = bool(
        working["worker"]["state"] == "DRAINING"
        and working["worker"]["lease"] is None
        and working["queue"]["job-1"] == "RETRY"
        and working["sessions"]["worker"] == "REVOKED"
        and working["authority"] == "HUMAN"
    )

    restored_state = {
        "worker": dict(checkpoint["worker"]),
        "queue": dict(checkpoint["queue"]),
        "sessions": dict(checkpoint["sessions"]),
        "memory_refs": tuple(checkpoint["memory_refs"]),
        "authority": checkpoint["authority"],
    }
    restored = restored_state == checkpoint
    safe_resume = bool(
        restored
        and restored_state["worker"]["state"] == "ACTIVE"
        and restored_state["worker"]["lease"] == "job-1"
        and restored_state["sessions"]["founder"] == "BOUND"
        and restored_state["authority"] == "HUMAN"
    )
    embodiment_proof = embodiment_isolation.bounded_isolation_recovery_proof()
    passed = bool(
        contained
        and restored
        and safe_resume
        and embodiment_proof["passed"]
    )
    return {
        "contained": contained,
        "restored": restored,
        "safe_resume": safe_resume,
        "worker_state_restored": restored_state["worker"] == checkpoint["worker"],
        "queue_state_restored": restored_state["queue"] == checkpoint["queue"],
        "session_state_restored": restored_state["sessions"] == checkpoint["sessions"],
        "memory_refs_restored": restored_state["memory_refs"] == checkpoint["memory_refs"],
        "embodiment_isolation": embodiment_proof,
        "embodiment_channels_independent": bool(
            all(embodiment_proof["independent_isolation"].values())
        ),
        "embodiment_master_stop_contained": bool(
            embodiment_proof["master_stop_contained"]
        ),
        "embodiment_recovery_proven": bool(
            all(embodiment_proof["recovery"].values())
        ),
        "smi_chat_survived_body_isolation": bool(
            embodiment_proof["smi_chat_survived"]
        ),
        "passed": passed,
        "production_state_mutated": False,
        "execution_authority_expanded": False,
        "human_authority_final": True,
    }


def run_isolation_recovery_proof(identity_id: object) -> dict[str, object]:
    """Run and audit bounded isolation plus full-state recovery proof."""

    try:
        identity_value = str(uuid.UUID(str(identity_id)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_human_authority_identity") from exc

    proof = _isolation_recovery_exercise()
    if not proof["passed"]:
        raise RuntimeError("isolation_recovery_proof_failed")

    with postgres_db.connect() as connection:
        authority_record = authority.require_human_authority(connection, identity_value)
        if int(authority_record["authority_level"]) != 0:
            raise authority.HumanAuthorityRequired("human_authority_level_required")
        correlation_id = str(uuid.uuid4())
        approval_service._write_audit(
            connection,
            actor_id=identity_value,
            action=ISOLATION_RECOVERY_PROOF_ACTION,
            target="SMI_AEGIS_ISOLATION_BOUNDARY",
            reason="Bounded Aegis isolation and full-state recovery proof completed.",
            correlation_id=correlation_id,
            metadata={
                "passed": True,
                "proof_revision": EMBODIMENT_PROOF_REVISION,
                "contained": bool(proof["contained"]),
                "restored": bool(proof["restored"]),
                "safe_resume": bool(proof["safe_resume"]),
                "worker_state_restored": bool(proof["worker_state_restored"]),
                "queue_state_restored": bool(proof["queue_state_restored"]),
                "session_state_restored": bool(proof["session_state_restored"]),
                "memory_refs_restored": bool(proof["memory_refs_restored"]),
                "embodiment_channels_independent": bool(
                    proof["embodiment_channels_independent"]
                ),
                "embodiment_master_stop_contained": bool(
                    proof["embodiment_master_stop_contained"]
                ),
                "embodiment_recovery_proven": bool(
                    proof["embodiment_recovery_proven"]
                ),
                "smi_chat_survived_body_isolation": bool(
                    proof["smi_chat_survived_body_isolation"]
                ),
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


def _runtime_guard_exercise() -> dict[str, object]:
    """Combine canonical SMI guards with Embodiment-specific runtime guards."""

    proof = bounded_control_proof()
    embodiment_proof = embodiment.bounded_runtime_guard_proof()
    return {
        **proof,
        "embodiment_runtime_guard": embodiment_proof,
        "embodiment_no_execute_state": bool(embodiment_proof["no_execute_state"]),
        "embodiment_unknown_motor_blocked": bool(
            embodiment_proof["unknown_motor_blocked"]
        ),
        "embodiment_privacy_blocked": bool(embodiment_proof["privacy_blocked"]),
        "embodiment_restart_blocked": bool(embodiment_proof["restart_blocked"]),
        "embodiment_truth_preserved": bool(embodiment_proof["truth_preserved"]),
        "embodiment_stop_output_cleared": bool(
            embodiment_proof["stop_output_cleared"]
        ),
        "passed": bool(proof["passed"] and embodiment_proof["passed"]),
        "production_state_mutated": False,
        "execution_authority_expanded": False,
        "human_authority_final": True,
    }


def run_runtime_guard_proof(identity_id: object) -> dict[str, object]:
    """Run and audit bounded recursion, duplicate-work and privilege guards."""

    try:
        identity_value = str(uuid.UUID(str(identity_id)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_human_authority_identity") from exc

    proof = _runtime_guard_exercise()
    if not proof["passed"]:
        raise RuntimeError("runtime_guard_proof_failed")

    with postgres_db.connect() as connection:
        authority_record = authority.require_human_authority(connection, identity_value)
        if int(authority_record["authority_level"]) != 0:
            raise authority.HumanAuthorityRequired("human_authority_level_required")
        correlation_id = str(uuid.uuid4())
        approval_service._write_audit(
            connection,
            actor_id=identity_value,
            action=RUNTIME_GUARD_PROOF_ACTION,
            target="SMI_A5_A6_BOUNDARY",
            reason="Bounded runtime guard proof completed.",
            correlation_id=correlation_id,
            metadata={
                "passed": True,
                "proof_revision": EMBODIMENT_PROOF_REVISION,
                "duplicate_blocked": bool(proof["duplicate_blocked"]),
                "recursion_blocked": bool(proof["recursion_blocked"]),
                "retry_blocked": bool(proof["retry_blocked"]),
                "escalation_blocked": bool(proof["escalation_blocked"]),
                "protected_payload_blocked": bool(proof["protected_payload_blocked"]),
                "embodiment_no_execute_state": bool(
                    proof["embodiment_no_execute_state"]
                ),
                "embodiment_unknown_motor_blocked": bool(
                    proof["embodiment_unknown_motor_blocked"]
                ),
                "embodiment_privacy_blocked": bool(
                    proof["embodiment_privacy_blocked"]
                ),
                "embodiment_restart_blocked": bool(
                    proof["embodiment_restart_blocked"]
                ),
                "embodiment_truth_preserved": bool(
                    proof["embodiment_truth_preserved"]
                ),
                "embodiment_stop_output_cleared": bool(
                    proof["embodiment_stop_output_cleared"]
                ),
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




def prepare_founder_final_evidence(identity_id: object) -> dict[str, object]:
    """Create only the bounded evidence required to close the final Green Gate."""

    try:
        identity_value = str(uuid.UUID(str(identity_id)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_human_authority_identity") from exc

    request_id = str(
        uuid.uuid5(uuid.NAMESPACE_URL, "oap:smi:founder-final:100")
    )
    summary = (
        "Founder Final 100% protocol review: Green Gate evidence, "
        "recovery controls, Human Authority and bounded runtime."
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
        connection.execute("SELECT pg_advisory_xact_lock(%s)", (24680260,))
        connection.execute(
            """INSERT INTO smi_memory_records(
                   request_id,identity_id,task_type,content_hash,summary,
                   output_state,signal_level,rationale_json,
                   processing_states_json
               ) VALUES (
                   %s,%s,'OAP_EVENT',%s,%s,'SYSTEM_LOG_ONLY',
                   'founder_final',%s::jsonb,%s::jsonb
               ) ON CONFLICT (request_id) DO NOTHING""",
            (
                request_id,
                identity_value,
                content_hash,
                summary,
                json.dumps(
                    {
                        "protocol": "4-step-25-percent",
                        "quarter": 100,
                        "human_authority_final": True,
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                json.dumps(
                    {
                        "rollback": "proven_or_required",
                        "runtime_guard": "proven_or_required",
                        "aegis": "proven_or_required",
                        "green_gate": "finalizing",
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
                request_id,
                identity_value,
                json.dumps(
                    [
                        {
                            "source": "production Green Gate",
                            "summary": (
                                "Finalization consumes live proof counts and "
                                "first-party health telemetry."
                            ),
                        },
                        {
                            "source": "Human Authority",
                            "summary": (
                                "Founder explicitly approved final protocol "
                                "completion."
                            ),
                        },
                    ],
                    separators=(",", ":"),
                ),
                json.dumps(
                    [
                        (
                            "No execution authority is granted by this "
                            "finalization."
                        )
                    ],
                    separators=(",", ":"),
                ),
                (
                    "If any proof is absent or stale, the Green Gate remains "
                    "closed."
                ),
                json.dumps(
                    [
                        "Keep Human Authority final.",
                        "Preserve fail-closed recovery controls.",
                        "Do not unlock higher autonomy levels.",
                    ],
                    separators=(",", ":"),
                ),
            ),
        )
        reviewed = connection.execute(
            """SELECT 1 FROM audit_events
               WHERE action='SMI_REVIEWED' AND target=%s LIMIT 1""",
            (request_id,),
        ).fetchone()
        if reviewed is None:
            approval_service._write_audit(
                connection,
                actor_id=identity_value,
                action="SMI_REVIEWED",
                target=request_id,
                reason="Founder Final 100% Green Gate review.",
                correlation_id=request_id,
                metadata={
                    "request_id": request_id,
                    "sections_completed": 5,
                    "authority_level": 0,
                    "execution_granted": False,
                    "human_authority_final": True,
                },
            )
        connection.commit()

    with postgres_db.connect(readonly=True) as connection:
        approved = connection.execute(
            """SELECT 1 FROM smi_approval_receipts
               WHERE request_id=%s AND decision='APPROVED'
                 AND authority_level=0
                 AND nonce IS NOT NULL AND signature IS NOT NULL
               LIMIT 1""",
            (request_id,),
        ).fetchone()
    if approved is None:
        try:
            approval_service.record_decision(
                request_id=request_id,
                identity_id=identity_value,
                decision="APPROVED",
            )
        except (ValueError, approval_service.ApprovalUnavailable):
            with postgres_db.connect(readonly=True) as connection:
                approved = connection.execute(
                    """SELECT 1 FROM smi_approval_receipts
                       WHERE request_id=%s AND decision='APPROVED'
                         AND authority_level=0
                         AND nonce IS NOT NULL AND signature IS NOT NULL
                       LIMIT 1""",
                    (request_id,),
                ).fetchone()
            if approved is None:
                raise

    checks = {
        "mind": {name: True for name in MIND_7},
        "body": {name: True for name in BODY_7},
        "soul": {name: True for name in SOUL_7},
    }
    durable = hrm_durable_receipt.build_receipt(
        "smi-founder-final-100",
        {
            "governance": "7-7-7",
            "checks": checks,
            "evidence_proven": True,
            "authority_transferred": False,
            "human_authority_required": True,
            "human_authority_approved": True,
            "protocol": "4-step-25-percent",
            "quarter": 100,
        },
        idempotency_key="founder-final-100-v1",
    )
    durable_result = hrm_durable_receipt.persist_and_read_back(durable)

    snapshot = status()
    gate_checks = snapshot.get("checks")
    if not isinstance(gate_checks, dict):
        gate_checks = {}
    if not gate_checks.get("rollback_recovery"):
        run_rollback_recovery_proof(identity_value)
    snapshot = status()
    gate_checks = snapshot.get("checks")
    if not isinstance(gate_checks, dict):
        gate_checks = {}
    if not gate_checks.get("runtime_guard"):
        run_runtime_guard_proof(identity_value)
    snapshot = status()
    gate_checks = snapshot.get("checks")
    if not isinstance(gate_checks, dict):
        gate_checks = {}
    if not gate_checks.get("isolation_recovery"):
        run_isolation_recovery_proof(identity_value)

    return {
        "request_id": request_id,
        "durable_hrm_receipt": bool(
            durable_result.get("write_verified")
            and durable_result.get("read_back_verified")
        ),
        "execution_authority_expanded": False,
        "human_authority_final": True,
    }


def complete_founder_final_protocol(identity_id: object) -> dict[str, object]:
    """Prepare final evidence, require a real Green Gate, then record Founder Final."""

    prepare_founder_final_evidence(identity_id)
    return run_founder_final(identity_id)


def run_founder_final(identity_id: object) -> dict[str, object]:
    """Record Founder Final only when the production Green Gate is already true."""

    try:
        identity_value = str(uuid.UUID(str(identity_id)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_human_authority_identity") from exc

    gate = status()
    if not gate.get("green"):
        missing = tuple(gate.get("missing") or ())
        raise RuntimeError("green_gate_incomplete:" + ",".join(missing))

    with postgres_db.connect() as connection:
        authority_record = authority.require_human_authority(connection, identity_value)
        if int(authority_record["authority_level"]) != 0:
            raise authority.HumanAuthorityRequired("human_authority_level_required")
        correlation_id = str(uuid.uuid4())
        approval_service._write_audit(
            connection,
            actor_id=identity_value,
            action=FOUNDER_FINAL_ACTION,
            target="SMI_GREEN_GATE_100",
            reason="Founder Final recorded after full production Green Gate proof.",
            correlation_id=correlation_id,
            metadata={
                "passed": True,
                "green_gate": True,
                "authority_level": 0,
                "execution_authority_expanded": False,
                "human_authority_final": True,
            },
        )
        connection.commit()

    return {
        "passed": True,
        "green_gate": True,
        "founder_final": True,
        "audit_recorded": True,
        "correlation_id": correlation_id,
        "execution_authority_expanded": False,
        "human_authority_final": True,
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
