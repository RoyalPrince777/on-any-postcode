"""Private-safe SMI completion and future intelligence contract.

This module does not claim AGI or ASI. It locks the governed SMI control layer,
then names Adaptive Coherent Intelligence as the next build layer with strict
Founder, Guardian, Green Gate and HRM boundaries.
"""
from __future__ import annotations

from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


SMI_LADDER = (
    {"level": "SMI", "name": "Sovereign Megaverse Intelligence", "state": "governed_control_layer", "claim_live": True},
    {"level": "ACI", "name": "Adaptive Coherent Intelligence", "state": "next_build_layer", "claim_live": False},
    {"level": "AGI", "name": "Artificial General Intelligence", "state": "future_target", "claim_live": False},
    {"level": "ASI", "name": "Artificial Super Intelligence", "state": "future_target", "claim_live": False},
    {"level": "Beyond", "name": "Civilisation / Megaverse Intelligence", "state": "vision_layer", "claim_live": False},
)

SMI_COMPLETION_CHECKS = (
    {"check": "War Room checks", "status": "built", "light": "🟢"},
    {"check": "404 debug", "status": "built", "light": "🟢"},
    {"check": "simple task debug", "status": "built", "light": "🟢"},
    {"check": "public/private boundary", "status": "guarded", "light": "🛡️"},
    {"check": "route proof", "status": "seed_proof_ready", "light": "🟡"},
    {"check": "map proof", "status": "surface_live_not_full_green", "light": "🟠"},
    {"check": "Movement proof", "status": "preview_only", "light": "🟡"},
    {"check": "Direct proof", "status": "connected_supplier_proof_needed", "light": "🟡"},
    {"check": "Live Pattern proof", "status": "proof_gated", "light": "🟡"},
    {"check": "payment lock", "status": "locked", "light": "🔒"},
    {"check": "dispatch lock", "status": "locked", "light": "🔒"},
    {"check": "hidden tracking block", "status": "blocked", "light": "⛔"},
    {"check": "fake green block", "status": "blocked_until_proof", "light": "🛑"},
    {"check": "7 visible SMI signals", "status": "built", "light": "🟢"},
    {"check": "HRM memory receipt fields", "status": "built", "light": "🟢"},
    {"check": "ACI ladder", "status": "locked_as_next_layer", "light": "🟢"},
)

ACI_BOUNDARY = {
    "name": "Adaptive Coherent Intelligence",
    "position": "after SMI, before any AGI/ASI claim",
    "can_do": (
        "adapt plans from HRM receipts",
        "keep system language coherent",
        "detect gaps across Maps, Travel, Movement, Spots, Direct and Live Pattern",
        "recommend next safe build steps",
        "surface contradictions before deploy",
        "prepare Founder decision packs",
    ),
    "cannot_do": (
        "self-approve",
        "claim AGI",
        "claim ASI",
        "deploy without approval/tool proof",
        "unlock payment",
        "unlock dispatch",
        "track hidden location",
        "override Guardian or Founder Authority",
    ),
}


def completion_status() -> dict[str, object]:
    """Return the private SMI completion contract."""

    return {
        "component": "SMI Completion Contract",
        "generated_at": _now(),
        "smi_finished_as": "governed_private_control_and_report_layer",
        "smi_not_finished_as": "full_autonomous_organism_or_AGI_or_ASI",
        "completion_checks": SMI_COMPLETION_CHECKS,
        "visible_signal_count": 7,
        "visible_signals": (
            "checking",
            "stage",
            "proof_needed",
            "locked",
            "blocked",
            "next_before_green",
            "hrm_memory",
        ),
        "ladder": SMI_LADDER,
        "aci_boundary": ACI_BOUNDARY,
        "6g_mind": "connected intelligence: live routes, maps, agents, voice, video, files and checks",
        "7g_mind": "coherent organism intelligence: adaptive, audited, proof-first and Founder-governed",
        "green_gate": {
            "smi_control_layer_green": True,
            "whole_product_green": False,
            "reason_whole_product_not_green": "real map tiles, route geometry, UK-wide data, events proof, traffic proof, receipts and live proof-runner checks remain incomplete",
        },
        "final_rule": "SMI can report, check, remember and recommend. Founder decides. Builder executes only after approval and proof.",
        "human_authority_final": True,
    }
