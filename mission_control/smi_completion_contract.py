"""Private-safe SMI completion contract.

SMI is one governed intelligence brain. A1 to A7 are its operating levels; they
are not agents, products, extra brains or claims of AGI/ASI. This contract reports
what is implemented in code separately from what still requires runtime, receipt,
audit, legal or Human Authority proof.
"""
from __future__ import annotations

from datetime import datetime, timezone

from . import autonomy_levels, intelligence_lenses


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

MISSING_PROOF_GATES = (
    {
        "id": "founder_chat_interaction",
        "name": "Authenticated Founder chat interaction",
        "state": "proof_required",
        "closes": "end-to-end proof that a signed Founder can submit an Intelligence command and receive a governed recorded response",
    },
    {
        "id": "hrm_receipt_chain",
        "name": "Production HRM receipt chain",
        "state": "proof_required",
        "closes": "durable recommendation, approval and outcome receipt evidence without inventing a decision",
    },
    {
        "id": "green_gate_aggregation",
        "name": "Green Gate evidence aggregation",
        "state": "proof_required",
        "closes": "real route, runtime, receipt, rollback and observability evidence feeding one truthful gate",
    },
    {
        "id": "rollback_recovery",
        "name": "Rollback and recovery",
        "state": "proof_required",
        "closes": "failure-path, restore and safe-resume evidence for any future A6 capability",
    },
    {
        "id": "observability",
        "name": "Live observability",
        "state": "proof_required",
        "closes": "fresh health, error and operational telemetry required before higher autonomy",
    },
    {
        "id": "a7_external",
        "name": "A7 external assurance",
        "state": "constitutional_lock",
        "closes": "external audit, legal/compliance proof, emergency halt proof, public/private proof and constitutional review",
    },
)


def completion_status() -> dict[str, object]:
    """Return the canonical private SMI completion contract."""
    autonomy = autonomy_levels.status()
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
        "missing_proof_gates": MISSING_PROOF_GATES,
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
            "authenticated_interaction": "proof_required",
            "receipt_chain": "proof_required",
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
                "Authenticated Founder interaction, production receipt-chain, Green Gate aggregation, "
                "rollback/recovery and live observability still require runtime evidence. A5-A7 remain locked."
            ),
        },
        "final_rule": (
            "Intelligence analyses and recommends. Guardian protects. Green Gate proves. "
            "HRM remembers. Human Authority decides. Higher A-levels never move authority."
        ),
        "human_authority_final": True,
    }
