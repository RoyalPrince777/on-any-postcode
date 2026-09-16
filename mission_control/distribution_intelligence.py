"""Founder-only OAP Distribution Intelligence contract.

Distribution Intelligence is a specialist capability inside Civilisation
Intelligence. It prepares and checks OAP-owned releases, campaigns, rights
evidence and destination readiness. It does not create an eighth Intelligence
World, a new agent family, or any independent execution authority. It does not
claim delivery to an external platform unless a real authenticated adapter and
receipt exist.
"""
from __future__ import annotations

from typing import Any

from . import live_signals

DISTRIBUTION_ID = "oap-distribution-intelligence"
DISTRIBUTION_NAME = "OAP Distribution Intelligence"
CANONICAL_WORLD_ID = "civilisation"
CANONICAL_WORLD_NAME = "Civilisation Intelligence"
CAPABILITY_KIND = "specialist_intelligence_capability"

CHECKS = (
    "release_draft",
    "rights_proof",
    "campaign_page",
    "merch_ticket_support_links",
    "human_approval",
    "external_route_proof",
    "public_claim_guard",
    "receipt_destination",
)

DESTINATIONS = (
    "OAP Music",
    "OAP Player",
    "OAP Radio",
    "OAP TV & Media",
    "OAP Records",
    "My Shop",
    "The Spot",
)

EXTERNAL_DESTINATIONS = (
    "Spotify",
    "Apple Music",
    "TikTok",
    "YouTube",
    "other external distribution partners",
)


def status() -> dict[str, Any]:
    validation = live_signals.validate_signal_language()
    return {
        "id": DISTRIBUTION_ID,
        "name": DISTRIBUTION_NAME,
        "ready": bool(validation.get("passed")),
        "kind": CAPABILITY_KIND,
        "canonical_world_id": CANONICAL_WORLD_ID,
        "canonical_world_name": CANONICAL_WORLD_NAME,
        "creates_new_world": False,
        "creates_agent_family": False,
        "mode": "prepare-check-route",
        "owned_destinations": DESTINATIONS,
        "external_destinations": EXTERNAL_DESTINATIONS,
        "checks": CHECKS,
        "core_signal_count": len(live_signals.LIVE_SIGNALS),
        "external_distribution_state": "locked_until_authenticated_adapter_and_receipt",
        "publishing_authority_granted": False,
        "payment_authority_granted": False,
        "external_execution_enabled": False,
        "rights_proof_required": True,
        "human_authority_final": True,
        "no_fake_green": True,
    }


def review_release(payload: object) -> dict[str, Any]:
    data = payload if isinstance(payload, dict) else {}
    title = " ".join(str(data.get("title") or "").split())[:240]
    rights_proof = bool(data.get("rights_proof"))
    campaign_ready = bool(data.get("campaign_ready"))
    approval = bool(data.get("human_approval"))
    external_adapter = bool(data.get("external_adapter_proven"))
    receipt = bool(data.get("receipt_destination"))

    gates = {
        "release_draft": bool(title),
        "rights_proof": rights_proof,
        "campaign_page": campaign_ready,
        "human_approval": approval,
        "external_route_proof": external_adapter,
        "receipt_destination": receipt,
        "public_claim_guard": True,
    }
    owned_ready = bool(title and rights_proof and campaign_ready and approval and receipt)
    external_ready = bool(owned_ready and external_adapter)
    return {
        "title": title,
        "canonical_world_id": CANONICAL_WORLD_ID,
        "canonical_world_name": CANONICAL_WORLD_NAME,
        "capability_kind": CAPABILITY_KIND,
        "gates": gates,
        "owned_oap_distribution_ready": owned_ready,
        "external_distribution_ready": external_ready,
        "state": "complete" if external_ready else ("working" if owned_ready else "warning"),
        "light": "✅" if external_ready else ("⏳" if owned_ready else "🟡"),
        "next": (
            "authenticated external adapter may execute only after a governed Human Authority action"
            if external_ready
            else "close missing proof gates; do not claim external delivery"
        ),
        "execution_performed": False,
        "publishing_authority_granted": False,
        "payment_authority_granted": False,
        "human_authority_final": True,
    }
