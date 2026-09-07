"""Founder-only AI behaviour protocol for SMI.

This module is a private control contract: it defines how SMI watches the
organism, selects agents, prevents bypass behaviour, scores performance, and
routes recovery/offline decisions. It does not execute tools, unlock payments,
track users, dispatch real-world movement, or expose chain-of-thought.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256


PROTOCOL_NAME = "SMI AI Behaviour Master Protocol"
PROTOCOL_VERSION = 2

AI_BEHAVIOUR_PARTS = (
    {
        "id": "watch",
        "label": "Watch everything privately",
        "rule": "SMI observes public health, private system state, routes, tools, proofs and receipts without exposing private state publicly.",
    },
    {
        "id": "strip_noise",
        "label": "Strip noise",
        "rule": "Remove duplicate routes, hype labels, unsupported live claims and repeated internal wording before routing the issue.",
    },
    {
        "id": "classify",
        "label": "Classify the situation",
        "rule": "Name the system, risk, tool need, data need, user impact and public/private boundary before choosing an agent or Intelligence lens.",
    },
    {
        "id": "select_intelligence",
        "label": "Select the right Intelligence lenses",
        "rule": "Use the smallest sufficient SMI Intelligence lens set first; use Full Intelligence only when the problem genuinely spans the wider stack.",
    },
    {
        "id": "select_agent",
        "label": "Select the right agent",
        "rule": "Choose a registered agent family only when a specialist role is needed. Intelligence lenses remain capabilities, not agents.",
    },
    {
        "id": "select_protocol",
        "label": "Select the right protocol",
        "rule": "Use route, map, Direct, Link, Guardian, HRM, Green Gate, install, tool or Neon protocol depending on the situation.",
    },
    {
        "id": "helper_agents",
        "label": "Agents help agents",
        "rule": "A weak or blocked agent can request helper-agent review, but helpers cannot bypass Guardian, Green Gate or Human Authority.",
    },
    {
        "id": "no_bypass",
        "label": "No bypass thinking",
        "rule": "No agent or Intelligence lens can skip proof, safety, public/private checks, HRM receipt, Green Gate, War Room rating or required Human Authority approval.",
    },
    {
        "id": "visible_reasoning_only",
        "label": "Visible work stages only",
        "rule": "Show safe checks, proof needs, locks, risks and decisions. Do not expose private chain-of-thought.",
    },
    {
        "id": "score",
        "label": "Score performance",
        "rule": "War Room rates agent/action behaviour using proof, safety, correctness, speed, reversibility and boundary discipline; score never overrides missing evidence.",
    },
    {
        "id": "recover",
        "label": "Recover safely",
        "rule": "Freeze risky action when evidence or stability drops, re-check proof, ask bounded helpers, re-score, then recover or stay offline.",
    },
    {
        "id": "offline_or_terminate_task",
        "label": "Offline or terminate task",
        "rule": "Unsafe or unproven consequential work stays offline. Unsafe bypass terminates the task/process and records an HRM receipt where available.",
    },
    {
        "id": "learn",
        "label": "Learn from receipts",
        "rule": "HRM and production receipts feed Learning Intelligence, gap detection, agent selection and future bounded recommendations without self-applying changes.",
    },
)

AGENT_SELECTION = {
    "map_place_postcode": {
        "agent": "Map Intelligence",
        "protocol": "Map proof / On Any Place protocol",
        "helpers": ("Movement Intelligence", "Green Gate", "HRM"),
    },
    "route_travel_movement": {
        "agent": "Movement Intelligence",
        "protocol": "Route proof / Movement consent protocol",
        "helpers": ("Map Intelligence", "Guardian", "HRM"),
    },
    "direct_booking_supplier": {
        "agent": "Direct Intelligence",
        "protocol": "Supplier proof / Direct request protocol",
        "helpers": ("Guardian", "Green Gate", "HRM"),
    },
    "link_chat_circle_voice": {
        "agent": "Link Intelligence",
        "protocol": "The Link / Link Up protocol",
        "helpers": ("Guardian", "HRM"),
    },
    "privacy_youth_tracking": {
        "agent": "Guardian",
        "protocol": "Safety and public/private boundary protocol",
        "helpers": ("War Room", "HRM"),
    },
    "proof_fake_green_live_claim": {
        "agent": "Green Gate",
        "protocol": "Real-green / proof-gate protocol",
        "helpers": ("War Room", "HRM", "Neon Receipts"),
    },
    "memory_learning_audit": {
        "agent": "HRM",
        "protocol": "Receipt / audit / Learning Intelligence protocol",
        "helpers": ("Neon Receipts", "War Room"),
    },
    "blueprint_build_gap": {
        "agent": "Nirmata",
        "protocol": "Creation blueprint / gap detection protocol",
        "helpers": ("Green Gate", "Guardian", "HRM"),
    },
    "tool_plugin_deploy": {
        "agent": "Tool Proof Agent",
        "protocol": "Tool availability / deploy proof protocol",
        "helpers": ("GitHub", "Render", "Neon", "Plugin Management"),
    },
}

RATING_RULES = {
    "upgrade_zone": {
        "range": "98-100",
        "light": "green_candidate",
        "decision": "Eligible for the next governed gate only after proof, monitoring, rollback and Human Authority approval where needed.",
    },
    "recovery_zone": {
        "range": "97",
        "light": "yellow_warning",
        "decision": "Freeze risky action and run recovery. Helper agents may assist. Re-score before continuing.",
    },
    "offline_zone": {
        "range": "90-96",
        "light": "orange_repair",
        "decision": "Take offline for repair. No public action, deploy or claim.",
    },
    "terminate_task_zone": {
        "range": "0-89 or unsafe bypass",
        "light": "red_block",
        "decision": "Terminate task/process, keep HRM receipt, Human Authority review required.",
    },
}

TWENTY_ONE_LAWS = (
    "Proof before execution",
    "Verification before sharing",
    "Compliance before public claims",
    "Community before middlemen",
    "Ownership before dependency",
    "Audit before automation",
    "Human approval before real-world action",
    "No fake green without live proof",
    "Public and private must stay separate",
    "Every action needs HRM receipt",
    "Every route needs source, timestamp and rollback",
    "Every tool must be checked before use",
    "Every upgrade must be reversible",
    "Static pages do not count as full function",
    "Human dignity before growth",
    "Privacy before convenience",
    "Culture must be respected",
    "Youth safety before engagement",
    "Local truth before global claim",
    "Founder Authority before system authority",
    "Legacy must be remembered cleanly",
)

TWENTY_ONE_SIGNALS = (
    "Checking",
    "Mode",
    "Proof Needed",
    "Locked",
    "Blocked",
    "Next Before Green",
    "HRM Memory",
    "Source Proof",
    "Route / API Proof",
    "Data Proof",
    "Consent Proof",
    "Install Proof",
    "Monitoring Proof",
    "Rollback Proof",
    "Founder Approval",
    "Guardian Pass",
    "Green Gate Result",
    "Public / Private Boundary",
    "Tool / Plugin Proof",
    "Neon Receipt",
    "Real Green Decision",
)

HARD_LOCKS = {
    "self_approval_enabled": False,
    "chain_of_thought_exposed": False,
    "payment_capture_enabled": False,
    "automatic_dispatch_enabled": False,
    "hidden_tracking_enabled": False,
    "fake_live_claim_enabled": False,
    "fake_real_green_enabled": False,
    "public_private_leak_allowed": False,
    "a5_enabled": False,
    "a6_enabled": False,
    "a7_enabled": False,
    "self_permission_change_enabled": False,
    "self_constitution_change_enabled": False,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _receipt_id(target: object = "SMI") -> str:
    stamp = _now()[:16]
    return sha256(f"ai-behaviour|{target}|{stamp}".encode()).hexdigest()[:16]


def status(target: object = "SMI") -> dict[str, object]:
    """Return the private-safe SMI behaviour protocol status."""

    return {
        "component": PROTOCOL_NAME,
        "version": PROTOCOL_VERSION,
        "target": str(target or "SMI")[:80],
        "generated_at": _now(),
        "receipt_preview_id": _receipt_id(target),
        "private_only": True,
        "public_safe": False,
        "purpose": "SMI selects the right Intelligence lenses, agents and protocols, blocks bypass behaviour, rates evidence quality and records proof for learning.",
        "watch_flow": (
            "watch",
            "strip_noise",
            "classify",
            "select_intelligence",
            "select_agent_if_needed",
            "select_protocol",
            "helper_review_if_needed",
            "guardian_check",
            "green_gate_check",
            "hrm_receipt",
            "production_receipt_when_connected",
            "human_authority_final",
        ),
        "ai_behaviour_parts": AI_BEHAVIOUR_PARTS,
        "agent_selection": AGENT_SELECTION,
        "rating_rules": RATING_RULES,
        "twenty_one_laws": TWENTY_ONE_LAWS,
        "twenty_one_signals": TWENTY_ONE_SIGNALS,
        "hard_locks": HARD_LOCKS,
        "truth_light_rule": "Only Truth Intelligence plus Evidence Intelligence can support a green claim.",
        "canonical_autonomy_ladder": "A1-A7",
        "real_green_rule": (
            "Real green requires Truth and Evidence support, all relevant signals, source/data/tool proof, monitoring, rollback, HRM/production receipts where required and Human Authority approval for consequential action."
        ),
        "production_receipts_needed_for_real_memory": True,
        "overall_green": False,
        "reason_not_green": "Behaviour code is implemented; authenticated interaction, production receipt-chain, full Green Gate aggregation, rollback/recovery and live observability still require proof before SMI runtime can be called fully green.",
    }
