"""Canonical read-only War Room projection and readiness-gap registry."""

from __future__ import annotations

from typing import Any

from oap.war_room import WarRoomEngine

WAR_ROOM_FLOW = (
    {"order": 1, "component": "SMI", "role": "Forms one recommendation"},
    {"order": 2, "component": "Guardian", "role": "Protects constitutional boundaries"},
    {"order": 3, "component": "War Room", "role": "Simulates bounded consequences"},
    {"order": 4, "component": "Human Authority", "role": "Approves or rejects"},
    {"order": 5, "component": "Living Kernel", "role": "Coordinates only an approved action"},
    {"order": 6, "component": "HRM", "role": "Records the complete outcome"},
)

REVIEW_LENSES = (
    {
        "id": "benefit",
        "name": "Benefit",
        "question": "What human or community value could this create?",
        "owner": "SMI",
    },
    {
        "id": "risk",
        "name": "Risk",
        "question": "What harm, abuse, privacy or constitutional risk could occur?",
        "owner": "Guardian",
    },
    {
        "id": "reversibility",
        "name": "Reversibility",
        "question": "Can the proposed change be safely rolled back?",
        "owner": "War Room",
    },
    {
        "id": "identity",
        "name": "Identity",
        "question": "Is the requester and their authority verified?",
        "owner": "Identity",
    },
    {
        "id": "memory",
        "name": "Memory",
        "question": "Is the evidence and decision trace complete?",
        "owner": "HRM",
    },
    {
        "id": "execution",
        "name": "Execution",
        "question": "Is there one bounded Builder handler and no bypass?",
        "owner": "Living Kernel",
    },
)

READINESS_GAPS = (
    {
        "id": "persistent_database",
        "priority": 1,
        "area": "Persistence",
        "owner": "HRM",
        "status": "Foundation in draft PR #5",
        "next_gate": "Merge, provision and migrate only after Human Authority approval",
    },
    {
        "id": "authenticated_identity",
        "priority": 2,
        "area": "Identity and security",
        "owner": "Identity",
        "status": "Not connected to the web session",
        "next_gate": "Implement keys, sessions, MFA, CSRF and authorization",
    },
    {
        "id": "approval_queue",
        "priority": 3,
        "area": "Human approval",
        "owner": "Human Authority",
        "status": "Internal receipt logic only",
        "next_gate": "Expose controls only after authenticated level-zero validation",
    },
    {
        "id": "provider_connection",
        "priority": 4,
        "area": "Ollama provider",
        "owner": "SMI Provider Router",
        "status": "Dashboard only; provider unassigned",
        "next_gate": "Approve one analysis-only provider connection",
    },
    {
        "id": "builder_handlers",
        "priority": 5,
        "area": "Execution",
        "owner": "Living Kernel",
        "status": "Zero default Builder actions",
        "next_gate": "Approve reversible handlers individually after security review",
    },
    {
        "id": "registry_activation",
        "priority": 6,
        "area": "Agent registry",
        "owner": "Registry",
        "status": "53 proposed passports remain disabled",
        "next_gate": "Approve names, roles and assignments individually",
    },
)


def validate_war_room_scope() -> dict[str, Any]:
    flow_components = [item["component"] for item in WAR_ROOM_FLOW]
    lens_ids = [item["id"] for item in REVIEW_LENSES]
    gap_ids = [item["id"] for item in READINESS_GAPS]
    errors: list[str] = []

    if len(flow_components) != len(set(flow_components)):
        errors.append("Duplicate system role in War Room flow")
    if len(lens_ids) != len(set(lens_ids)):
        errors.append("Duplicate War Room review lens")
    if len(gap_ids) != len(set(gap_ids)):
        errors.append("Duplicate readiness gap")
    if flow_components.count("Human Authority") != 1:
        errors.append("War Room must preserve one final Human Authority gate")
    if "War Room" not in flow_components:
        errors.append("War Room simulation chamber is missing")

    return {
        "passed": not errors,
        "errors": tuple(errors),
        "checks": {
            "flow_components": len(flow_components),
            "review_lenses": len(lens_ids),
            "readiness_gaps": len(gap_ids),
            "duplicate_system_roles": len(flow_components) - len(set(flow_components)),
            "duplicate_lenses": len(lens_ids) - len(set(lens_ids)),
            "duplicate_gaps": len(gap_ids) - len(set(gap_ids)),
            "final_authority": "Human Authority",
        },
    }


def get_public_war_room() -> dict[str, Any]:
    """Return architecture and readiness facts without running a simulation."""

    validation = validate_war_room_scope()
    engine = WarRoomEngine().status()
    return {
        "validation": validation,
        "engine": engine,
        "flow": WAR_ROOM_FLOW if validation["passed"] else (),
        "review_lenses": REVIEW_LENSES if validation["passed"] else (),
        "gaps": READINESS_GAPS if validation["passed"] else (),
        "allowed_outputs": (
            "RECOMMENDATION_READY",
            "REVIEW_REQUIRED",
            "BLOCK_REQUEST",
            "SYSTEM_LOG_ONLY",
        ),
        "controls_enabled": False,
        "independent_decision_authority": False,
        "human_authority": "Final approval required",
    }
