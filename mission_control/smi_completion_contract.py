"""Private-safe SMI completion contract.

SMI is one governed intelligence brain. A1 to A7 are its operating levels; they
are not agents, products or extra brains. Code readiness and production proof are
reported separately. Runtime evidence is read-only and fails closed when the
production store cannot be inspected.
"""
from __future__ import annotations

from datetime import datetime, timezone

from . import autonomy_levels, intelligence_lenses, postgres_db


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


SMI_COMPLETION_CHECKS = (
    {"check": "Founder-only Mission Control boundary", "status": "implemented", "light": "🟢", "proof_class": "code"},
    {"check": "Personal SMI streaming chat", "status": "implemented", "light": "🟢", "proof_class": "code"},
    {"check": "stop / mic / plus / history / code controls", "status": "implemented", "light": "🟢", "proof_class": "code"},
    {"check": "safe visible work stages", "status": "implemented", "light": "🟢", "proof_class": "code"},
    {"check": "26 Intelligence lenses", "status": "implemented", "light": "🟢", "proof_class": "code"},
    {"check": "Intelligence command router", "status": "implemented", "light": "🟢", "proof_class": "code"},
    {"check": "War Room and evidence runner", "status": "implemented", "light": "🟢", "proof_class": "code"},
    {"check": "Guardian / Aegis fail-closed boundary", "status": "implemented", "light": "🟢", "proof_class": "code"},
    {"check": "HRM conversation persistence", "status": "implemented", "light": "🟢", "proof_class": "code"},
    {"check": "Judgement / Human Authority gate", "status": "implemented", "light": "🟢", "proof_class": "code"},
    {"check": "A1-A7 autonomy constitution", "status": "implemented", "light": "🟢", "proof_class": "code"},
    {"check": "A5 preparation boundary", "status": "locked_until_proof", "light": "🔒", "proof_class": "governance"},
    {"check": "A6 governed execution", "status": "future_locked", "light": "🔒", "proof_class": "governance"},
    {"check": "A7 organism-scale autonomy", "status": "constitutional_locked", "light": "🔒", "proof_class": "governance"},
    {"check": "production HRM / approval receipt evidence", "status": "live_proof_required", "light": "🟡", "proof_class": "runtime"},
    {"check": "real Green Gate aggregation", "status": "live_proof_required", "light": "🟡", "proof_class": "runtime"},
    {"check": "rollback and recovery evidence", "status": "live_proof_required", "light": "🟡", "proof_class": "runtime"},
    {"check": "live observability evidence", "status": "live_proof_required", "light": "🟡", "proof_class": "runtime"},
    {"check": "external audit / legal / compliance for A7", "status": "external_proof_required", "light": "🔒", "proof_class": "external"},
)

PROOF_GATE_DEFINITIONS = (
    {
        "id": "founder_chat_interaction",
        "name": "Authenticated Founder chat interaction",
        "closes": "a level-zero Human Authority SMI review is present in the production audit trail",
    },
    {
        "id": "hrm_receipt_chain",
        "name": "Production HRM receipt chain",
        "closes": "durable recommendation, five-section Judgement and signed Human Authority decision receipt exist",
    },
    {
        "id": "green_gate_aggregation",
        "name": "Green Gate evidence aggregation",
        "closes": "real route, runtime, receipt, rollback and observability evidence feed one truthful gate",
    },
    {
        "id": "rollback_recovery",
        "name": "Rollback and recovery",
        "closes": "failure-path, restore and safe-resume evidence exists for any future A6 capability",
    },
    {
        "id": "observability",
        "name": "Live observability",
        "closes": "fresh health, error and operational telemetry is attached to the governed release gate",
    },
    {
        "id": "a7_external",
        "name": "A7 external assurance",
        "closes": "external audit, legal/compliance proof, emergency halt proof, public/private proof and constitutional review exist",
    },
)


def _runtime_evidence() -> dict[str, object]:
    """Read non-sensitive SMI evidence counts from production, failing closed."""
    evidence: dict[str, object] = {
        "store_reachable": False,
        "authority_conversations": 0,
        "authority_user_messages": 0,
        "authority_memory_records": 0,
        "authority_smi_review_audits": 0,
        "five_section_reviews": 0,
        "approval_receipts": 0,
        "signed_approved_receipts": 0,
        "active_human_authorities": 0,
        "audit_events": 0,
        "error": None,
    }
    if not postgres_db.configured():
        evidence["error"] = "production_store_not_configured"
        return evidence
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT
                  (SELECT COUNT(*) FROM smi_conversations c
                    JOIN oap_identities i ON i.identity_id=c.identity_id
                    WHERE i.status='ACTIVE' AND i.identity_type='HUMAN_AUTHORITY'),
                  (SELECT COUNT(*) FROM smi_messages m
                    JOIN smi_conversations c ON c.conversation_id=m.conversation_id
                    JOIN oap_identities i ON i.identity_id=c.identity_id
                    WHERE i.status='ACTIVE' AND i.identity_type='HUMAN_AUTHORITY' AND m.role='user'),
                  (SELECT COUNT(*) FROM smi_memory_records m
                    JOIN oap_identities i ON i.identity_id=m.identity_id
                    WHERE i.status='ACTIVE' AND i.identity_type='HUMAN_AUTHORITY'),
                  (SELECT COUNT(*) FROM audit_events
                    WHERE authority_level=0 AND action='SMI_REVIEWED'),
                  (SELECT COUNT(*) FROM smi_judgement_reviews WHERE sections_completed=5),
                  (SELECT COUNT(*) FROM smi_approval_receipts),
                  (SELECT COUNT(*) FROM smi_approval_receipts
                    WHERE decision='APPROVED' AND authority_level=0
                      AND nonce IS NOT NULL AND signature IS NOT NULL),
                  (SELECT COUNT(*) FROM oap_identities
                    WHERE status='ACTIVE' AND identity_type='HUMAN_AUTHORITY'),
                  (SELECT COUNT(*) FROM audit_events)"""
            ).fetchone()
        if row is not None:
            keys = (
                "authority_conversations",
                "authority_user_messages",
                "authority_memory_records",
                "authority_smi_review_audits",
                "five_section_reviews",
                "approval_receipts",
                "signed_approved_receipts",
                "active_human_authorities",
                "audit_events",
            )
            evidence.update({key: int(value or 0) for key, value in zip(keys, row)})
            evidence["store_reachable"] = True
    except Exception:  # noqa: BLE001 - completion truth must fail closed.
        evidence["error"] = "production_evidence_unavailable"
    return evidence


def _proof_gates(evidence: dict[str, object]) -> tuple[dict[str, object], ...]:
    founder_proven = bool(
        evidence.get("store_reachable")
        and int(evidence.get("active_human_authorities") or 0) > 0
        and int(evidence.get("authority_smi_review_audits") or 0) > 0
        and int(evidence.get("authority_memory_records") or 0) > 0
    )
    receipt_chain_proven = bool(
        evidence.get("store_reachable")
        and int(evidence.get("five_section_reviews") or 0) > 0
        and int(evidence.get("signed_approved_receipts") or 0) > 0
    )
    proof = {
        "founder_chat_interaction": founder_proven,
        "hrm_receipt_chain": receipt_chain_proven,
        "green_gate_aggregation": False,
        "rollback_recovery": False,
        "observability": False,
        "a7_external": False,
    }
    rows: list[dict[str, object]] = []
    for item in PROOF_GATE_DEFINITIONS:
        gate_id = str(item["id"])
        proven = bool(proof[gate_id])
        rows.append(
            {
                **item,
                "state": "proven" if proven else ("constitutional_lock" if gate_id == "a7_external" else "proof_required"),
                "light": "🟢" if proven else ("🔒" if gate_id == "a7_external" else "🟡"),
                "proven": proven,
            }
        )
    return tuple(rows)


def completion_status() -> dict[str, object]:
    """Return canonical code truth plus live non-sensitive production evidence."""
    autonomy = autonomy_levels.status()
    evidence = _runtime_evidence()
    gates = _proof_gates(evidence)
    missing = tuple(item for item in gates if not item["proven"])
    founder_proven = next(item for item in gates if item["id"] == "founder_chat_interaction")["proven"]
    receipt_proven = next(item for item in gates if item["id"] == "hrm_receipt_chain")["proven"]
    return {
        "component": "SMI Completion Contract",
        "generated_at": _now(),
        "identity": "Sovereign Megaverse Intelligence",
        "one_brain": True,
        "operating_level_model": "A1-A7",
        "configured_level": autonomy["configured_level"],
        "autonomy_levels": autonomy["canonical_levels"],
        "completion_checks": SMI_COMPLETION_CHECKS,
        "intelligence": {
            "lens_count": len(intelligence_lenses.FULL_LENS_IDS),
            "core_lens_count": len(intelligence_lenses.CORE_LENS_IDS),
            "full_lens_ids": intelligence_lenses.FULL_LENS_IDS,
            "core_lens_ids": intelligence_lenses.CORE_LENS_IDS,
            "chat_routing": "implemented",
            "execution_granted_by_lens": False,
        },
        "runtime_evidence": evidence,
        "proof_gates": gates,
        "missing_proof_gates": missing,
        "hard_locks": {
            "a5_enabled": autonomy["a5_enabled"],
            "a6_enabled": autonomy["a6_enabled"],
            "a7_enabled": autonomy["a7_enabled"],
            "payment_or_value_transfer": False,
            "real_world_dispatch": False,
            "unreviewed_deploy": False,
            "production_database_migration": False,
            "self_permission_change": False,
            "self_constitution_change": False,
        },
        "truth_light": {
            "code_surface": "green",
            "authenticated_interaction": "green" if founder_proven else "proof_required",
            "receipt_chain": "green" if receipt_proven else "proof_required",
            "green_gate": "proof_required",
            "a5": "locked",
            "a6": "locked",
            "a7": "locked",
            "whole_smi_runtime": "not_full_green",
        },
        "green_gate": {
            "code_boundary_ready": True,
            "smi_runtime_full_green": False,
            "reason_not_full_green": (
                "Signed Human Authority decision receipts, Green Gate aggregation, rollback/recovery and "
                "live operational observability still require proof. A5-A7 remain locked."
                if founder_proven
                else "Authenticated Human Authority interaction, signed decision receipts, Green Gate aggregation, rollback/recovery and observability still require proof. A5-A7 remain locked."
            ),
        },
        "final_rule": (
            "Intelligence analyses and recommends. Guardian protects. Green Gate proves. "
            "HRM remembers. Human Authority decides. Higher A-levels never move authority."
        ),
        "human_authority_final": True,
    }
