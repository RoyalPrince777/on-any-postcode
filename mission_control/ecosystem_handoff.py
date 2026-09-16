"""Canonical OAP product handoff path.

The Link, Market, Media, Distribution and OAP Store keep separate ownership and
permissions while sharing one auditable continuation path. A handoff is navigation
and evidence only: it never creates a payment, publishes uncleared media, delivers
to an external platform or installs software automatically.
"""
from __future__ import annotations

from collections.abc import Mapping


class HandoffBlocked(RuntimeError):
    """A product handoff does not have the required evidence."""


ECOSYSTEM_PATH: tuple[dict[str, object], ...] = (
    {
        "id": "the_link",
        "name": "The Link",
        "entry": "/the-link",
        "purpose": "Communication, opportunities and governed relationship context.",
        "requires": ("identity",),
    },
    {
        "id": "market",
        "name": "Market",
        "entry": "/the-spot/market",
        "purpose": "Owned listings, products, services and creator commerce discovery.",
        "requires": ("identity", "merchant_or_creator_context"),
    },
    {
        "id": "media_distribution",
        "name": "Media / Distribution",
        "entry": "/the-spot/distribution",
        "purpose": "Rights-aware OAP-first media, campaign and release preparation.",
        "requires": ("identity", "creator_context", "rights_proof"),
    },
    {
        "id": "oap_store",
        "name": "OAP Store",
        "entry": "service:ownpost-store",
        "purpose": "Certified OAP apps, games, tools and creator software packages.",
        "requires": ("identity", "certification", "package_proof"),
    },
)

HARD_LOCKS = {
    "payment_capture": False,
    "external_distribution": False,
    "automatic_install": False,
    "permission_transfer": False,
    "authority_transfer": False,
}


def path_status() -> dict[str, object]:
    return {
        "path": tuple(dict(item) for item in ECOSYSTEM_PATH),
        "stage_ids": tuple(str(item["id"]) for item in ECOSYSTEM_PATH),
        "one_way_order": True,
        "hard_locks": dict(HARD_LOCKS),
        "human_authority_final": True,
    }


def handoff(
    current_stage: object,
    next_stage: object,
    *,
    evidence: Mapping[str, bool],
) -> dict[str, object]:
    """Validate one adjacent product handoff without transferring permissions."""

    current = str(current_stage or "").strip()
    target = str(next_stage or "").strip()
    stage_ids = [str(item["id"]) for item in ECOSYSTEM_PATH]
    if current not in stage_ids or target not in stage_ids:
        raise HandoffBlocked("unknown_ecosystem_stage")
    current_index = stage_ids.index(current)
    if current_index + 1 >= len(stage_ids) or stage_ids[current_index + 1] != target:
        raise HandoffBlocked("adjacent_handoff_required")

    destination = ECOSYSTEM_PATH[current_index + 1]
    required = tuple(str(item) for item in destination["requires"])
    missing = tuple(name for name in required if evidence.get(name) is not True)
    if missing:
        raise HandoffBlocked("missing_handoff_evidence:" + ",".join(missing))

    return {
        "from": current,
        "to": target,
        "destination": destination["entry"],
        "required_evidence": required,
        "evidence_proven": True,
        "permission_transferred": False,
        "authority_transferred": False,
        "payment_captured": False,
        "external_distribution_performed": False,
        "automatic_install_performed": False,
        "human_authority_final": True,
    }
