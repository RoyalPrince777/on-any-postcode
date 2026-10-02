"""Founder-only unified SMI Command Dashboard projection.

This module composes existing canonical status sources. It creates no new
authority, runtime, registry, proof system, or duplicate intelligence model.
"""
from __future__ import annotations

from typing import Any

from oap.smi.action_risk_router import status as action_risk_status

from . import (
    all_intelligence,
    brain,
    intelligence_runtime_proof,
    prince_sovereign_bank,
    sika_account_engine,
    sika_pay_gateway,
    sika_payment_orchestrator,
    war_room,
)


def status() -> dict[str, Any]:
    brain_status = brain.get_public_brain_status()
    war_status = war_room.get_war_room_dashboard()
    intelligence = all_intelligence.public_safe_status()
    runtime = intelligence_runtime_proof.status()
    risk = action_risk_status()
    bank_identity = prince_sovereign_bank.status()
    account = sika_account_engine.status()
    pay = sika_pay_gateway.status()
    orchestrator = sika_payment_orchestrator.status()

    war_summary = war_status.get("summary") or {}
    war_validation = war_status.get("validation") or {}
    autonomy = brain_status.get("autonomy") or {}

    return {
        "component": "SMI Founder Command Dashboard",
        "brain": {
            "count": brain_status.get("brain_count"),
            "regions": brain_status.get("regions"),
            "lenses": brain_status.get("intelligence_lenses"),
            "core_lenses": brain_status.get("core_intelligence_lenses"),
            "mode": brain_status.get("mode"),
        },
        "intelligence": {
            "worlds": intelligence.get("world_count"),
            "families": intelligence.get("family_count"),
            "agents": intelligence.get("agent_count"),
            "agent_target": intelligence.get("agent_target"),
            "architecture_light": intelligence.get("architecture_light"),
            "routing_light": intelligence.get("routing_light"),
            "memory_light": intelligence.get("memory_light"),
        },
        "runtime": {
            "bounded_worlds": runtime.get("bounded_runtime_proven"),
            "bounded_total": runtime.get("bounded_runtime_total"),
            "live_worlds": runtime.get("live_external_proven"),
            "live_total": runtime.get("live_external_total"),
            "full_worlds": runtime.get("full_runtime_proven"),
            "full_total": runtime.get("full_runtime_total"),
            "universal_runtime_green": runtime.get("universal_runtime_green"),
        },
        "war_room": {
            "validation_passed": bool(war_validation.get("passed")),
            "rated_areas": int(war_summary.get("rated_areas") or 0),
            "overall_evidence_score": int(war_summary.get("overall_evidence_score") or 0),
            "runtime_verified": int(war_summary.get("runtime_verified") or 0),
            "operationally_certified": int(war_summary.get("operationally_certified") or 0),
        },
        "risk_router": risk,
        "bank": {
            "name": bank_identity.get("name"),
            "heritage_name": bank_identity.get("banking_family"),
            "software_controls_present": True,
            "account_engine_present": bool(account.get("persistent_account_identity")),
            "single_pay_gateway": bool(pay.get("single_payment_door")),
            "rights_record_required": bool(pay.get("rights_record_required")),
            "orchestrator_present": bool(orchestrator.get("persistent_payment_intent")),
            "direct_authorisation_bypass_allowed": bool(
                orchestrator.get("direct_authorisation_bypass_allowed", False)
            ),
            "regulated_execution_enabled": bool(
                bank_identity.get("regulated_execution_enabled")
            ),
            "operational_bank": bool(bank_identity.get("operational_bank")),
            "licence_verified": bool(bank_identity.get("licence_verified")),
            "provider_calling": bool(pay.get("provider_calling")),
            "settlement_execution": bool(pay.get("settlement_execution")),
            "money_movement": bool(pay.get("money_movement")),
            "human_authority_final": True,
        },
        "autonomy": {
            "configured_level": autonomy.get("configured_level"),
            "a3_policy_ready": autonomy.get("a3_policy_ready"),
            "a4_enabled": autonomy.get("a4_enabled"),
            "a5_enabled": autonomy.get("a5_enabled"),
            "a6_enabled": autonomy.get("a6_enabled"),
            "a7_enabled": autonomy.get("a7_enabled"),
            "human_authority_final": autonomy.get("human_authority_final"),
        },
        "doors": (
            {"name": "Live SMI", "href": "/mission/ollama"},
            {"name": "Brain", "href": "/mission/brain"},
            {"name": "War Room", "href": "/mission/war-room"},
            {"name": "All Intelligence", "href": "/mission/intelligence"},
            {"name": "Judgement", "href": "/mission/judgement"},
        ),
        "execution_granted": False,
        "approval_granted": False,
        "human_authority_final": True,
        "truth_boundary": (
            "This dashboard aggregates canonical evidence only. Built, runtime-verified, "
            "live-external and operationally-certified remain separate claims."
        ),
    }
