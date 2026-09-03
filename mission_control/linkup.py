"""Canonical governed model for OAP Link Up communications.

Link Up is the protected conversation product inside The Link communications
gateway, not a second Messenger engine. Its approved dashboard views remain
Directory, Inbox and Community Power so ownership and validation rules do not
drift when user-facing language evolves. Public projections expose presentation
copy only; authenticated message records remain owned by the existing
Communications product store and are scoped to the signed-in identity.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

COMMUNICATIONS_SYSTEM = "Communications"
COMMUNITY_POWER_SYSTEM = "Community Power"

LINK_UP_LANGUAGE_LAW: tuple[str, ...] = (
    "Brand language for identity.",
    "Human language for conversation.",
    "Plain language for safety.",
    "Local character without global confusion.",
)

LINK_UP_PUBLIC_VOCABULARY: dict[str, str] = {
    "product": "Link Up",
    "conversations": "Link Ups",
    "people": "People",
    "connection": "Link",
    "connection_request": "Link Request",
    "group": "Crew",
    "group_host": "Crew Host",
    "new_conversation": "Start a Link Up",
    "join": "Link In",
    "invite": "Bring In",
    "leave": "Step Out",
    "presence": "Around Now",
    "available": "I'm Free",
    "delivered": "Landed",
    "read": "Seen",
    "voice_note": "Voice",
    "audio_call": "Call",
    "video_call": "Face Up",
    "share_location": "Share My Spot",
    "live_location": "Live Spot",
    "short_status": "Now",
    "status_prompt": "What you on?",
    "notifications": "Alerts",
    "announcement": "Signal",
    "profile": "My Card",
    "trust_status": "Certified",
    "trusted_contact": "Trusted Contact",
}

LINK_UP_PLAIN_SAFETY_TERMS: tuple[str, ...] = (
    "Block",
    "Report",
    "Privacy",
    "Security",
    "Emergency",
    "Delete",
    "Settings",
)

LINK_DASHBOARD_VIEWS: tuple[dict[str, str], ...] = (
    {
        "id": "directory",
        "name": "Directory",
        "owner": COMMUNICATIONS_SYSTEM,
        "ownership": "owned_view",
        "purpose": "Find verified people and local connections.",
        "status": "Protected",
        "data": "Authenticated member projection only",
        "boundary": (
            "People and community connections only; this is not the Agent "
            "Intelligence directory."
        ),
    },
    {
        "id": "inbox",
        "name": "Inbox",
        "owner": COMMUNICATIONS_SYSTEM,
        "ownership": "owned_view",
        "purpose": "Private conversation access for authenticated members.",
        "status": "Protected",
        "data": "Sender and recipient scoped messages only",
        "boundary": (
            "A view over approved Communications records, not a second Mail "
            "or Messenger store."
        ),
    },
    {
        "id": "community_power",
        "name": "Community Power",
        "owner": COMMUNITY_POWER_SYSTEM,
        "ownership": "linked_view",
        "purpose": "Entry point to World Rooms and approved Pulse Spaces.",
        "status": "Read-only link",
        "data": "No private room or contribution records exposed",
        "boundary": (
            "A linked entry point only; contribution and reputation records "
            "remain owned by Community Power."
        ),
    },
)

LOCKED_LINK_VIEW_IDS = tuple(view["id"] for view in LINK_DASHBOARD_VIEWS)
LOCKED_LINK_VIEW_NAMES = tuple(view["name"] for view in LINK_DASHBOARD_VIEWS)

EXPECTED_VIEW_OWNERS = {
    "directory": (COMMUNICATIONS_SYSTEM, "owned_view"),
    "inbox": (COMMUNICATIONS_SYSTEM, "owned_view"),
    "community_power": (COMMUNITY_POWER_SYSTEM, "linked_view"),
}

RELATED_COMMUNICATION_BOUNDARIES: tuple[dict[str, str], ...] = (
    {
        "id": "signals",
        "name": "Signal",
        "owner": "OAP World",
        "relationship": (
            "Public announcements remain Signal; they are not private "
            "conversations or Inbox messages."
        ),
    },
    {
        "id": "pulse",
        "name": "Pulse",
        "owner": "OAP World",
        "relationship": (
            "Pulse remains the community heartbeat and may link into approved "
            "threads without becoming another message store."
        ),
    },
    {
        "id": "team_rooms",
        "name": "OAP TV Team Rooms",
        "owner": "OAP TV",
        "relationship": (
            "Existing match-room conversations stay on their current surface; "
            "this dashboard does not copy them."
        ),
    },
    {
        "id": "mail_notifications",
        "name": "Mail, Alerts and Broadcasts",
        "owner": COMMUNICATIONS_SYSTEM,
        "relationship": (
            "They remain sibling Communications modules; Inbox does not "
            "replace or duplicate them."
        ),
    },
    {
        "id": "identity_guardian_hrm",
        "name": "Identity, Guardian and HRM",
        "owner": "Shared protective systems",
        "relationship": (
            "Identity validates access, Guardian protects privacy and youth "
            "safety, and HRM receives approved audit metadata only."
        ),
    },
)

PRIVACY_PATH: tuple[dict[str, str], ...] = (
    {"name": "Identity", "action": "Validates the member"},
    {"name": "Permissions", "action": "Scopes conversation access"},
    {"name": "Guardian", "action": "Protects privacy and youth safety"},
    {"name": "Link Up", "action": "Presents the approved conversation view"},
    {"name": "HRM", "action": "Receives approved audit metadata only"},
)

PROTECTED_LINK_RUNTIME: dict[str, object] = {
    "authenticated_identity_required": True,
    "csrf_required_for_mutations": True,
    "sender_recipient_scope": True,
    "message_persistence": "Postgres Communications store",
    "rate_limit_enabled": True,
    "guardian_message_screening": True,
    "read_receipts": True,
    "public_message_projection": False,
    "human_authority_final": True,
}

REMAINING_LINK_GATES: tuple[dict[str, str], ...] = (
    {
        "title": "Blocking and reporting workflow",
        "description": (
            "Add durable block/report state, moderation routing and auditable "
            "Guardian escalation before broader membership rollout."
        ),
        "status": "Not yet certified",
    },
    {
        "title": "Private-message retention and encryption policy",
        "description": (
            "Certify storage encryption, retention/deletion behaviour and "
            "backup handling for protected Communications records."
        ),
        "status": "Not yet certified",
    },
    {
        "title": "World Rooms participation",
        "description": (
            "Reference approved World Rooms without copying contribution, "
            "reputation or private conversation records."
        ),
        "status": "Not yet certified",
    },
)

# Compatibility alias for older internal projections.
PROPOSED_LINK_ENABLEMENT = REMAINING_LINK_GATES


def _normalise(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def _duplicates(values: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def validate_link_scope(
    views: Iterable[Mapping[str, Any]] = LINK_DASHBOARD_VIEWS,
) -> dict[str, Any]:
    """Detect duplicate views, ownership transfers and public mutation drift."""

    view_list = tuple(views)
    ids = [str(view.get("id", "")).strip().casefold() for view in view_list]
    names = [_normalise(str(view.get("name", ""))) for view in view_list]
    duplicate_ids = _duplicates(ids)
    duplicate_names = _duplicates(names)
    missing = set(LOCKED_LINK_VIEW_IDS) - set(ids)
    unexpected = set(ids) - set(LOCKED_LINK_VIEW_IDS)
    mutation_controls = sum(bool(view.get("mutation_enabled")) for view in view_list)

    ownership_conflicts: list[str] = []
    for view in view_list:
        view_id = str(view.get("id", "")).strip().casefold()
        expected = EXPECTED_VIEW_OWNERS.get(view_id)
        if expected is None:
            continue
        actual = (str(view.get("owner", "")), str(view.get("ownership", "")))
        if actual != expected:
            ownership_conflicts.append(view_id)

    errors: list[str] = []
    if duplicate_ids:
        errors.append("Duplicate Link view IDs: " + ", ".join(sorted(duplicate_ids)))
    if duplicate_names:
        errors.append(
            "Duplicate Link view names: " + ", ".join(sorted(duplicate_names))
        )
    if missing:
        errors.append("Locked Link views missing: " + ", ".join(sorted(missing)))
    if unexpected:
        errors.append("Unapproved Link views present: " + ", ".join(sorted(unexpected)))
    if ownership_conflicts:
        errors.append(
            "Link view ownership conflict: "
            + ", ".join(sorted(set(ownership_conflicts)))
        )
    if mutation_controls:
        errors.append("Public The Link mutation controls must remain disabled")

    communication_views = sum(
        view.get("ownership") == "owned_view" for view in view_list
    )
    linked_views = sum(view.get("ownership") == "linked_view" for view in view_list)

    return {
        "passed": not errors,
        "errors": errors,
        "checks": {
            "dashboard_views": len(view_list),
            "communication_views": communication_views,
            "linked_views": linked_views,
            "duplicate_ids": len(duplicate_ids),
            "naming_conflicts": len(duplicate_names),
            "ownership_conflicts": len(set(ownership_conflicts)),
            "mutation_controls": mutation_controls,
        },
    }


def get_public_link_dashboard() -> dict[str, Any]:
    """Return only visitor-facing Link Up copy."""

    return {
        "product_name": LINK_UP_PUBLIC_VOCABULARY["product"],
        "tagline": "Your people. Your Link Ups. Your community.",
        "law": "The Spot → The Link → Link Up",
        "features": [
            {
                "name": LINK_UP_PUBLIC_VOCABULARY["people"],
                "purpose": "Find your people and connections.",
            },
            {
                "name": LINK_UP_PUBLIC_VOCABULARY["conversations"],
                "purpose": "Keep up with private conversations.",
            },
            {
                "name": "Crews",
                "purpose": "Bring selected people together in private groups.",
            },
        ],
    }
