"""Canonical live-working intelligence profile for Founder SMI.

This profile unifies existing OAP intelligence capabilities into one governed
runtime identity. It is deliberately not an AGI achievement claim and does not
expand execution authority. "Live-working" means the system may continuously
reason, observe, coordinate, adapt plans, prepare OAP-owned work and record
bounded internal evidence through existing governed contracts while external or
consequential actions remain Human Authority gated.
"""
from __future__ import annotations

from typing import Any

from oap.smi.agi_core import AGICore
from oap.smi.command_intelligence import CommandIntelligence

from . import coherent_automation, distribution_intelligence, oap_system_protocol

PROFILE_ID = "oap-live-working-intelligence"
PROFILE_NAME = "OAP Live Working Intelligence"
RUNTIME_MODE = "live_working"
AUTONOMY_CLASS = "A4_supervised_live_working"

CAPABILITY_STACK: tuple[dict[str, str], ...] = (
    {"id": "smi", "name": "Sovereign Megaverse Intelligence", "role": "reasoning, challenge and bounded judgement"},
    {"id": "omni", "name": "OMNI", "role": "whole-system awareness without permission expansion"},
    {"id": "hybrid", "name": "HYBRID", "role": "minimum-safe path selection across deterministic, local AI, connected service and Human Authority paths"},
    {"id": "civilisation", "name": "Civilisation Intelligence", "role": "coordination across systems, intelligence worlds, formations and agents"},
    {"id": "adaptive", "name": "Adaptive General Intelligence", "role": "evidence-driven replanning without silently mutating approved consequential work"},
    {"id": "coherent", "name": "Coherent Automation", "role": "21-signal plan-route-check-receipt coordination"},
    {"id": "distribution", "name": "Distribution Intelligence", "role": "OAP-owned release, rights, destination and receipt readiness"},
    {"id": "agi", "name": "AGI Core", "role": "bounded cross-world routing and synthesis target; not an achieved-AGI claim"},
    {"id": "guardian", "name": "Guardian / Aegis", "role": "security, privacy, consent, permission and safety boundary"},
    {"id": "hrm", "name": "HRM", "role": "durable evidence, receipts, outcomes and learning"},
)


def status() -> dict[str, Any]:
    """Return a secret-free truth projection of the unified live-working mode."""

    agi = AGICore().status()
    command = CommandIntelligence().status()
    coherent = coherent_automation.status()
    distribution = distribution_intelligence.status()

    adaptive_ready = bool(
        command.get("ready")
        and "adgi" in tuple(command.get("command_path") or ())
        and command.get("adaptive_mutates_approved_action") is False
    )
    coherent_ready = bool(coherent.get("ready") and coherent.get("signals_valid"))
    distribution_ready = bool(distribution.get("ready"))
    agi_routing_ready = bool(agi.get("ready") and agi.get("canonical_world_model"))

    working = bool(
        adaptive_ready and coherent_ready and distribution_ready and agi_routing_ready
    )

    return {
        "id": PROFILE_ID,
        "name": PROFILE_NAME,
        "mode": RUNTIME_MODE,
        "state": "working" if working else "attention",
        "light": "🔵" if working else "🟡",
        "live_working": working,
        "read_only": False,
        "autonomy_class": AUTONOMY_CLASS,
        "capability_stack": CAPABILITY_STACK,
        "protocol_flow": tuple(layer.value for layer in oap_system_protocol.CANONICAL_FLOW),
        "adaptive_ready": adaptive_ready,
        "coherent_ready": coherent_ready,
        "distribution_ready": distribution_ready,
        "agi_routing_ready": agi_routing_ready,
        "seven_world_model": bool(agi.get("canonical_world_model")),
        "world_count": int(agi.get("world_count") or 0),
        "general_intelligence_capability_count": int(
            command.get("total_general_intelligence_capabilities") or 0
        ),
        "agi_target": True,
        "agi_achieved": False,
        "general_intelligence_certified": False,
        "internal_governed_work_enabled": True,
        "live_evidence_reads": True,
        "adaptive_replanning_enabled": adaptive_ready,
        "oap_owned_preparation_enabled": distribution_ready,
        "durable_internal_writes": "existing governed application contracts only",
        "external_consequential_execution": False,
        "independent_approval": False,
        "silent_authority_escalation": False,
        "execution_boundary": (
            "External or consequential action requires the existing Guardian, Green Gate, "
            "authenticated adapter, receipt path and Human Authority controls."
        ),
        "human_authority_final": True,
        "no_fake_green": True,
        "truth_boundary": (
            "Live-working describes active governed system operation. AGI Core and general-"
            "intelligence capability names describe routing and reasoning architecture; they "
            "do not assert that OAP has achieved or certified artificial general intelligence."
        ),
    }
