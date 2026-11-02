"""Bounded Matrix Signal Bus for auditable inter-agent communication.

Registered Matrix agents communicate by emitting Signals into the Matrix System.
The bus routes Signals for coordination and review only. It never grants execution,
self-approval, permission changes, agent creation, or Human Authority bypass.

Extended Matrix names that are still under passport review remain visible to the
Founder but cannot emit live Matrix Signals until separately registered.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from . import agent_passport_audit, agents

CORE_MATRIX_ORDER: tuple[str, ...] = (
    "Neo",
    "Morpheus",
    "Trinity",
    "Oracle",
    "Architect",
    "Keymaker",
    "Seraph",
)

EXTENDED_REVIEW_ORDER: tuple[str, ...] = (
    "Tank",
    "Dozer",
    "Agent Smith",
    "Twinz",
    "Niobe",
    "Apoc",
    "Switch",
    "Ghost",
)

MATRIX_ROLE_CHANNELS: dict[str, str] = {
    "Neo": "recovery_and_anomaly",
    "Morpheus": "truth_and_false_green",
    "Trinity": "coordination",
    "Oracle": "consequence_and_forecast",
    "Architect": "structure_and_dependency",
    "Keymaker": "permitted_route",
    "Seraph": "trust_and_boundary",
    "Tank": "operations_control",
    "Dozer": "infrastructure_and_resilience",
    "Agent Smith": "integrity_and_corruption",
    "Twinz": "dual_path_contradiction",
    "Niobe": "movement_and_route_command",
    "Apoc": "failure_and_collapse_warning",
    "Switch": "mode_and_state_transition_review",
    "Ghost": "quiet_observation_and_anomaly_review",
}

MATRIX_COMMUNICATION_LAW: tuple[str, ...] = (
    "Agents send Signals, not hidden commands.",
    "Matrix System routes Signals through an auditable envelope.",
    "Trinity coordinates multi-agent work without becoming final authority.",
    "SMI interprets the consolidated intelligence pack.",
    "HRM records consequential decisions and evidence receipts.",
    "Guardian protects safety, privacy and authority boundaries.",
    "War Room reviews consequential decisions.",
    "Human Authority remains final.",
)

SYSTEM_RECIPIENTS: tuple[str, ...] = (
    "Matrix System",
    "SMI",
    "HRM Core",
    "Guardian",
    "Green Gate",
    "War Room",
    "Human Authority",
)

ALLOWED_URGENCY: tuple[str, ...] = ("low", "normal", "high", "critical")


def _now() -> str:
    return datetime.now(UTC).isoformat()


def registered_matrix_names() -> tuple[str, ...]:
    """Return the canonical registered Matrix team in locked order."""

    names = {
        str(agent["name"])
        for agent in agents.AGENT_REGISTRY
        if agent["family_id"] == "matrix"
    }
    return tuple(name for name in CORE_MATRIX_ORDER if name in names)


def extended_review_names() -> tuple[str, ...]:
    """Return selected Matrix extension names that remain in passport review."""

    candidates = {
        str(item["name"]): str(item["status"])
        for item in agent_passport_audit.MATRIX_EXTENDED_CANDIDATES
    }
    return tuple(
        name
        for name in EXTENDED_REVIEW_ORDER
        if candidates.get(name) == "passport_review"
    )


def topology() -> dict[str, Any]:
    """Return a side-effect-free Matrix communication topology projection."""

    registered = set(registered_matrix_names())
    review = set(extended_review_names())
    participants = []
    for name in CORE_MATRIX_ORDER + EXTENDED_REVIEW_ORDER:
        status = (
            "registered"
            if name in registered
            else "passport_review"
            if name in review
            else "unavailable"
        )
        participants.append(
            {
                "name": name,
                "channel": MATRIX_ROLE_CHANNELS[name],
                "status": status,
                "can_emit_signal": status == "registered",
                "can_execute": False,
                "home": agents.matrix_home_for(name),
            }
        )

    return {
        "name": "Matrix Signal Bus",
        "system": "Matrix System",
        "mode": "founder_governed_signal_routing",
        "communication_law": MATRIX_COMMUNICATION_LAW,
        "participants": tuple(participants),
        "registered_count": len(registered),
        "extended_review_count": len(review),
        "coordinator": "Trinity",
        "interpreter": "SMI",
        "memory": "HRM Core",
        "protector": "Guardian",
        "proof_gate": "Green Gate",
        "consequential_review": "War Room",
        "final_authority": "Human Authority",
        "execution_granted": False,
        "full_green": False,
    }


def _normalise_recipients(recipients: Iterable[str] | None) -> tuple[str, ...]:
    if recipients is None:
        return ("Trinity", "SMI")
    result = tuple(
        dict.fromkeys(str(item).strip() for item in recipients if str(item).strip())
    )
    if not result:
        return ("Trinity", "SMI")
    allowed = set(registered_matrix_names()) | set(SYSTEM_RECIPIENTS)
    unknown = tuple(item for item in result if item not in allowed)
    if unknown:
        raise ValueError(
            "Unknown or unregistered Matrix recipient: " + ", ".join(unknown)
        )
    return result


def route_signal(
    *,
    sender: str,
    topic: str,
    kind: str = "analysis",
    recipients: Iterable[str] | None = None,
    urgency: str = "normal",
    confidence: float | None = None,
    evidence: Iterable[str] = (),
    requested_action: str = "review",
    consequential: bool = False,
) -> dict[str, Any]:
    """Create a bounded Matrix Signal envelope without taking external action."""

    if not isinstance(sender, str):
        raise ValueError("Signal sender must be text")
    if not isinstance(topic, str) or not topic.strip() or len(topic) > 2000:
        raise ValueError("Signal topic must be 1-2000 characters")
    if not isinstance(kind, str) or len(kind) > 64:
        raise ValueError("Invalid signal kind")
    if not isinstance(requested_action, str) or len(requested_action) > 256:
        raise ValueError("Invalid requested action")
    if recipients is not None and (isinstance(recipients, (str, bytes)) or not isinstance(recipients, (tuple, list)) or len(recipients) > 16 or any(not isinstance(x, str) for x in recipients)):
        raise ValueError("Recipients must be at most 16 named entries")
    if isinstance(evidence, (str, bytes)) or not isinstance(evidence, (tuple, list)) or len(evidence) > 16 or any(not isinstance(x, str) or len(x) > 1000 for x in evidence):
        raise ValueError("Evidence must be at most 16 bounded text entries")
    sender = sender.strip()
    if sender not in registered_matrix_names():
        raise ValueError(
            f"{sender or 'Unknown sender'} is not a registered Matrix agent"
        )
    if urgency not in ALLOWED_URGENCY:
        raise ValueError("Unsupported urgency")
    topic = topic.strip()
    if not topic:
        raise ValueError("Signal topic is required")
    if confidence is not None and (isinstance(confidence, bool) or not isinstance(confidence, (float, int)) or not 0 <= confidence <= 1):
        raise ValueError("confidence must be between 0 and 1")

    routed_recipients = _normalise_recipients(recipients)
    evidence_items = tuple(
        str(item).strip() for item in evidence if str(item).strip()
    )
    delivery_path = tuple(
        dict.fromkeys(
            (
                sender,
                "Matrix System",
                "Trinity",
                *routed_recipients,
                "SMI",
            )
        )
    )

    return {
        "signal_id": f"MATRIX-SIGNAL-{uuid4().hex[:12].upper()}",
        "timestamp_utc": _now(),
        "sender": sender,
        "sender_home": agents.matrix_home_for(sender),
        "recipient_homes": {name: agents.matrix_home_for(name) for name in routed_recipients if name in registered_matrix_names()},
        "delivered_to_agent_runtime": False,
        "recipient_reply_received": False,
        "sender_channel": MATRIX_ROLE_CHANNELS[sender],
        "topic": topic,
        "kind": kind.strip() or "analysis",
        "urgency": urgency,
        "confidence": confidence,
        "evidence": evidence_items,
        "requested_action": requested_action.strip() or "review",
        "recipients": routed_recipients,
        "delivery_path": delivery_path,
        "state": "routed_for_review",
        "trinity_coordination_required": True,
        "smi_interpretation_required": True,
        "hrm_receipt_required": True,
        "guardian_required": True,
        "green_gate_required": True,
        "war_room_required": consequential,
        "human_authority_required": consequential,
        "human_authority_final": True,
        "execution_granted": False,
        "external_action_taken": False,
        "self_approval_allowed": False,
        "permission_change_allowed": False,
        "agent_creation_allowed": False,
    }


def route_reply_signal(*, original: dict[str, Any], sender: str,
                       topic: str, evidence: Iterable[str] = ()) -> dict[str, Any]:
    """Prepare a correlated review reply, without impersonation or live delivery.

    A caller must be separately authorised to speak for the sender. This function
    checks the original envelope's recipient scope, not external identity.
    """
    if not isinstance(original, dict) or not str(original.get("signal_id", "")).startswith("MATRIX-SIGNAL-"):
        raise ValueError("Valid Matrix signal required")
    if original.get("sender") not in registered_matrix_names():
        raise ValueError("Original sender must be registered")
    if sender not in registered_matrix_names():
        raise ValueError("Reply sender must be registered")
    if sender not in original.get("recipients", ()):
        raise ValueError("Reply sender must be a registered original recipient")
    if not isinstance(topic, str) or not topic.strip() or len(topic) > 2000:
        raise ValueError("Reply topic must be 1-2000 characters")
    reply = route_signal(
        sender=sender, topic=topic,
        kind="review_reply",
        recipients=(original["sender"],),
        evidence=evidence,
        consequential=bool(original.get("war_room_required")),
    )
    reply["in_reply_to"] = original["signal_id"]
    reply["delivery_confirmed"] = False
    reply["independent_agent_execution_proven"] = False
    return reply
