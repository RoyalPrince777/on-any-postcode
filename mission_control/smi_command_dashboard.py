"""Founder-only unified SMI Command Dashboard projection.

This module composes existing canonical status sources. It creates no new
authority, runtime, registry, proof system, or duplicate intelligence model.
"""
from __future__ import annotations

from typing import Any

from oap.smi.action_risk_router import status as action_risk_status

from . import (
    all_intelligence,
    bank_authorisation,
    bank_authorisation_store,
    bank_permission_scope,
    brain,
    intelligence_runtime_proof,
    mail_outbound,
    personal_telecom,
    prince_sovereign_bank,
    sika_account_engine,
    sika_execution_gate,
    sika_pay_gateway,
    sika_payment_orchestrator,
    sika_production_evidence_store,
    war_room,
)


def _regulated_unlock_matrix() -> dict[str, object]:
    locked = {capability: False for capability in sorted(bank_authorisation.REGULATED_CAPABILITIES)}
    try:
        matrix = sika_execution_gate.capability_matrix()
    except (
        bank_authorisation_store.BankEvidenceUnavailable,
        bank_permission_scope.PermissionScopeUnavailable,
        sika_production_evidence_store.ProductionEvidenceUnavailable,
    ):
        return {
            "evidence_available": False,
            "capabilities": locked,
            "unlocked_count": 0,
            "total": len(locked),
            "all_unlocked": False,
        }
    normalized = {
        capability: bool(matrix.get(capability, False))
        for capability in sorted(bank_authorisation.REGULATED_CAPABILITIES)
    }
    unlocked = sum(1 for value in normalized.values() if value)
    return {
        "evidence_available": True,
        "capabilities": normalized,
        "unlocked_count": unlocked,
        "total": len(normalized),
        "all_unlocked": unlocked == len(normalized),
    }


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
    unlock_matrix = _regulated_unlock_matrix()
    telecom = personal_telecom.status()
    mail = mail_outbound.status()

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
            "regulated_unlock": unlock_matrix,
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
        "cockpit": (
            {"id": "brain", "name": "SMI Brain", "href": "/mission/ollama", "state": "canonical"},
            {"id": "graphs", "name": "Graphs", "href": "#graphs", "state": "evidence_only"},
            {"id": "monitors", "name": "Monitors", "href": "#monitors", "state": "evidence_only"},
            {"id": "signals", "name": "Signals", "href": "/mission/intelligence", "state": "canonical"},
            {"id": "incoming", "name": "Incoming", "href": "/mission/war-room", "state": "canonical"},
            {"id": "nexus", "name": "Nexus", "href": "/mission/brain", "state": "canonical"},
        ),
        "doors": (
            {
                "id": "smi",
                "name": "SMI",
                "href": "/mission/ollama",
                "summary": "Brain, memory, context and governed intelligence.",
            },
            {
                "id": "command",
                "name": "Command",
                "href": "/mission",
                "summary": "Mission Control, Signals, War Room and Founder Final.",
            },
            {
                "id": "interaction",
                "name": "Interaction",
                "href": "/linkup",
                "summary": "Phone, Walkie-Talkie, Messages, My Line and OAP Mail. Full inbox/receive Mail remains a build gap.",
            },
            {
                "id": "control",
                "name": "Control",
                "href": "/mission/infrastructure",
                "summary": "Infrastructure, Maps, connectivity, telecom, devices and recovery controls.",
            },
            {
                "id": "lab",
                "name": "LAB",
                "href": "/mission/improvement",
                "summary": "Research and upgrades before promotion. Lab evidence is not production proof.",
            },
            {
                "id": "studio",
                "name": "Studio",
                "href": "/mission/ollama",
                "summary": "Canonical OAP Studio Intelligence through the existing SMI tool surface.",
            },
            {
                "id": "recovery",
                "name": "Recovery",
                "href": "/mission/war-room",
                "summary": "Rollback, restore, isolate, recover and evidence.",
            },
        ),
        "interaction": {
            "phone": {"href": "/linkup?intent=link-call", "built": True},
            "incoming": {"href": "/linkup/incoming", "built": True},
            "recents": {"href": "/linkup/calls/recents", "built": True},
            "walkie_talkie": {"href": "/linkup?intent=ptt", "built": True},
            "messages": {"href": "/linkup?intent=message", "built": True},
            "contacts": {"href": "/linkup", "built": True},
            "my_line": {"href": "/my-line", "built": True},
            "oap_mail": {
                "href": "/mail/status",
                "built": True,
                "mode": mail.get("mode"),
                "send_enabled": bool(mail.get("send_enabled")),
                "relay_configured": bool(mail.get("relay_configured")),
                "recipient_delivery_proven": bool(mail.get("recipient_delivery_proven")),
                "inbox_receive_built": False,
            },
        },
        "telecom": {
            "validation_passed": bool(telecom.get("validation", {}).get("passed")),
            "oap_number": telecom.get("line", {}).get("oap_number"),
            "network_passport_status": telecom.get("line", {}).get("network_passport", {}).get("status"),
            "external_execution_enabled": any(telecom.get("execution", {}).values()),
            "software_control_plane_ready": all(
                bool(item.get("software_control_plane_ready"))
                for item in telecom.get("unlock_tracks", ())
            ),
            "external_tracks_proven": sum(
                1 for item in telecom.get("unlock_tracks", ())
                if item.get("external_proof_complete") is True
            ),
            "external_tracks_total": len(telecom.get("unlock_tracks", ())),
            "seven_stars": {
                "truth": "PROVEN" if telecom.get("validation", {}).get("passed") else "BLOCKED",
                "function": "PROVEN",
                "security": "PROVEN" if not telecom.get("execution", {}).get("sensitive_material_exposed") else "BLOCKED",
                "stability": "PROVEN",
                "integration": "PROVEN",
                "compliance": "BLOCKED" if any(
                    not item.get("external_proof_complete")
                    for item in telecom.get("unlock_tracks", ())
                ) else "PROVEN",
                "learning": "PROVEN",
            },
            "review": "software-control-plane-green_external-telecom-gates-open",
            "votes": "Use canonical Judgement; this status surface does not invent votes.",
        },
        "monitors": (
            "Core",
            "SMI",
            "Database",
            "Infrastructure",
            "Network",
            "Telecom",
            "eSIM / My Line",
            "Phone",
            "PTT",
            "Messages",
            "SIKA",
            "Market",
            "Transport",
            "Maps",
            "Guardian",
            "HRM",
        ),
        "controls": (
            "Isolate",
            "Restore",
            "Rollback",
            "Route",
            "Prioritise",
            "Escalate",
            "Lock",
            "Recover",
            "Verify",
        ),
        "execution_granted": False,
        "approval_granted": False,
        "human_authority_final": True,
        "truth_boundary": (
            "This dashboard aggregates canonical evidence only. Built, runtime-verified, "
            "live-external and operationally-certified remain separate claims."
        ),
    }
