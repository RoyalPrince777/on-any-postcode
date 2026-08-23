"""Canonical, read-only model for the OAP communications dashboard.

LinkUp is the protected conversation product inside The Link communications
gateway, not a second Messenger engine. Its approved dashboard views are Directory, Inbox and Community Power.
Community Power is linked into the dashboard without transferring ownership.
This module exposes no identities, message bodies, persistence or send path.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

COMMUNICATIONS_SYSTEM = "Communications"
COMMUNITY_POWER_SYSTEM = "Community Power"

LINK_DASHBOARD_VIEWS: tuple[dict[str, str], ...] = (
    {
        "id": "directory",
        "name": "Directory",
        "owner": COMMUNICATIONS_SYSTEM,
        "ownership": "owned_view",
        "purpose": "Find verified people and local connections.",
        "status": "Identity required",
        "data": "No member identities exposed",
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
        "status": "Unavailable",
        "data": "No private messages exposed",
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
        "purpose": "Entry point to community rooms and postcode Pulse Spaces.",
        "status": "Not connected",
        "data": "No room or contribution records exposed",
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
        "name": "Signals",
        "owner": "OAP World",
        "relationship": (
            "Public announcements remain Signals; they are not private "
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
        "name": "Mail, Notifications and Broadcasts",
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
    {"name": "LinkUp", "action": "Presents the approved conversation view"},
    {"name": "HRM", "action": "Receives approved audit metadata only"},
)

PROPOSED_LINK_ENABLEMENT: tuple[dict[str, str], ...] = (
    {
        "title": "Connect Identity and Permissions",
        "description": (
            "Require authenticated identity, conversation membership and "
            "object-level authorization before Directory or Inbox data exists."
        ),
        "status": "Requires human approval",
    },
    {
        "title": "Approve private-message protection",
        "description": (
            "Define encryption, retention, blocking, reporting, rate limits "
            "and Guardian youth-safety checks before a send control is added."
        ),
        "status": "Requires human approval",
    },
    {
        "title": "Link approved Pulse Spaces",
        "description": (
            "Reference Community Power rooms without copying contribution, "
            "reputation or private conversation records."
        ),
        "status": "Requires human approval",
    },
)


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
    """Detect duplicate views, ownership transfers and operational controls."""

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
        errors.append("The Link mutation controls must remain disabled")

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
    """Return an allowlisted shell containing no people or conversations."""

    return {
        "product_name": "LinkUp",
        "tagline": "Simple chat. Talk local. Build global.",
        "law": "Inside The Spot → The Link → LinkUp. Create bridges, not barriers.",
        "views": [dict(view) for view in LINK_DASHBOARD_VIEWS],
        "related_systems": [
            dict(system) for system in RELATED_COMMUNICATION_BOUNDARIES
        ],
        "privacy_path": [dict(step) for step in PRIVACY_PATH],
        "proposed_enablement": [dict(item) for item in PROPOSED_LINK_ENABLEMENT],
        "validation": validate_link_scope(),
        "operating_mode": {
            "label": "Read-only privacy shell",
            "message": (
                "No directory identities, room records or private messages "
                "are loaded."
            ),
        },
        "human_authority": {
            "status": "Final architecture approval required",
            "message": (
                "No communication engine, data connection or send control is "
                "enabled by this dashboard."
            ),
        },
    }
