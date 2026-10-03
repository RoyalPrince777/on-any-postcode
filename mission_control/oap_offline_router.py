"""Canonical offline/degraded routing for the OAP Digital Organism.

Every major OAP domain receives an explicit offline route. The router describes
what may continue locally, what may queue for later reconciliation, and what
must remain blocked until live external verification returns.

It does not cache private browser data, grant execution authority, or claim that
a route is physically available merely because its policy is defined.
"""
from __future__ import annotations

from typing import Any

OFFLINE_MODES = (
    "LOCAL_READ_WRITE",
    "LOCAL_READ_ONLY",
    "LOCAL_ANALYSIS",
    "QUEUE_ONLY",
    "BLOCKED_LIVE_REQUIRED",
)

ROUTES: tuple[dict[str, Any], ...] = (
    {
        "domain": "infrastructure",
        "mode": "LOCAL_READ_ONLY",
        "local_capabilities": ("health_snapshot", "config_readback", "recovery_plan"),
        "queued_capabilities": ("runtime_evidence_sync",),
        "blocked_capabilities": ("production_deploy", "provider_change"),
    },
    {
        "domain": "trust_identity",
        "mode": "LOCAL_READ_ONLY",
        "local_capabilities": ("cached_identity_context", "permission_readback"),
        "queued_capabilities": ("identity_audit_sync",),
        "blocked_capabilities": ("new_identity_certification", "role_change"),
    },
    {
        "domain": "world_spot",
        "mode": "LOCAL_READ_ONLY",
        "local_capabilities": ("cached_public_world", "cached_places", "draft_post"),
        "queued_capabilities": ("public_post_intent",),
        "blocked_capabilities": ("public_publish",),
    },
    {
        "domain": "link_up",
        "mode": "QUEUE_ONLY",
        "local_capabilities": ("draft_message", "local_conversation_context"),
        "queued_capabilities": ("message_send_intent",),
        "blocked_capabilities": ("message_delivery_claim", "link_call"),
    },
    {
        "domain": "music",
        "mode": "LOCAL_READ_WRITE",
        "local_capabilities": ("owned_download_playback", "catalogue_draft", "rights_draft"),
        "queued_capabilities": ("release_sync", "rights_evidence_sync"),
        "blocked_capabilities": ("public_release", "royalty_payout"),
    },
    {
        "domain": "commerce_market",
        "mode": "LOCAL_ANALYSIS",
        "local_capabilities": ("offer_analysis", "unit_economics", "basket_draft", "inventory_snapshot"),
        "queued_capabilities": ("order_intent", "catalogue_change_intent"),
        "blocked_capabilities": ("payment_capture", "live_inventory_claim", "public_price_change"),
    },
    {
        "domain": "sika",
        "mode": "LOCAL_READ_ONLY",
        "local_capabilities": ("ledger_readback", "payment_draft", "reconciliation_draft"),
        "queued_capabilities": ("payment_intent_review",),
        "blocked_capabilities": ("money_transfer", "settlement", "regulated_execution"),
    },
    {
        "domain": "post_core",
        "mode": "QUEUE_ONLY",
        "local_capabilities": ("parcel_draft", "service_request_draft"),
        "queued_capabilities": ("carrier_handoff_intent",),
        "blocked_capabilities": ("carrier_handoff", "live_tracking_claim"),
    },
    {
        "domain": "movement",
        "mode": "LOCAL_ANALYSIS",
        "local_capabilities": ("cached_route_context", "offline_route_plan", "movement_draft"),
        "queued_capabilities": ("booking_or_dispatch_intent",),
        "blocked_capabilities": ("driver_dispatch", "live_traffic_claim", "booking_confirmation"),
    },
    {
        "domain": "media_studio",
        "mode": "LOCAL_READ_WRITE",
        "local_capabilities": ("local_edit", "draft_render", "asset_workspace"),
        "queued_capabilities": ("publish_intent", "cloud_render_intent"),
        "blocked_capabilities": ("public_publish", "external_distribution"),
    },
    {
        "domain": "youth",
        "mode": "LOCAL_READ_ONLY",
        "local_capabilities": ("cached_safety_guidance", "local_safeguarding_rules"),
        "queued_capabilities": ("safeguarding_evidence_sync",),
        "blocked_capabilities": ("external_contact", "current_rule_claim_without_freshness"),
    },
    {
        "domain": "nature",
        "mode": "LOCAL_READ_ONLY",
        "local_capabilities": ("cached_nature_content", "observation_draft"),
        "queued_capabilities": ("observation_sync",),
        "blocked_capabilities": ("live_environment_claim",),
    },
    {
        "domain": "arena",
        "mode": "LOCAL_READ_WRITE",
        "local_capabilities": ("local_gameplay", "checkpoint", "result_draft"),
        "queued_capabilities": ("result_sync",),
        "blocked_capabilities": ("public_ranking_update", "prize_payment"),
    },
    {
        "domain": "intelligence_governance",
        "mode": "LOCAL_ANALYSIS",
        "local_capabilities": (
            "smi_local_reasoning",
            "hormozi_offline",
            "evidence_review",
            "coherence_review",
            "recovery_review",
        ),
        "queued_capabilities": ("evidence_receipt_sync", "learning_candidate_sync"),
        "blocked_capabilities": (
            "self_approval",
            "self_deploy",
            "permission_change",
            "founder_final_impersonation",
        ),
    },
)

_BY_DOMAIN = {route["domain"]: route for route in ROUTES}


def route_for(domain: str, capability: str = "") -> dict[str, Any]:
    """Return the bounded offline decision for one OAP domain/capability."""

    key = str(domain or "").strip().casefold()
    route = _BY_DOMAIN.get(key)
    if route is None:
        return {
            "domain": key,
            "decision": "BLOCK",
            "reason": "unknown_domain",
            "offline": True,
            "external_action_permitted": False,
            "human_authority_final": True,
        }

    ability = str(capability or "").strip()
    if not ability:
        return {
            **route,
            "decision": "ROUTE_DEFINED",
            "offline": True,
            "external_action_permitted": False,
            "human_authority_final": True,
        }
    if ability in route["local_capabilities"]:
        decision = "LOCAL"
    elif ability in route["queued_capabilities"]:
        decision = "QUEUE"
    elif ability in route["blocked_capabilities"]:
        decision = "BLOCK"
    else:
        decision = "BLOCK"
    return {
        "domain": key,
        "capability": ability,
        "mode": route["mode"],
        "decision": decision,
        "offline": True,
        "requires_reconciliation": decision == "QUEUE",
        "external_action_permitted": False,
        "human_authority_final": True,
    }


def reconciliation_policy() -> dict[str, object]:
    return {
        "flow": (
            "local_state",
            "connectivity_returns",
            "verify_remote_freshness",
            "detect_conflict",
            "reconcile",
            "human_review_if_material_conflict",
            "sync_receipt",
        ),
        "silent_overwrite_allowed": False,
        "stale_claim_promoted_to_live": False,
        "queued_intent_equals_execution": False,
        "human_authority_final": True,
    }


def status() -> dict[str, Any]:
    domains = tuple(route["domain"] for route in ROUTES)
    return {
        "name": "OAP Offline Route Fabric",
        "domain_count": len(ROUTES),
        "domains": domains,
        "unique_domains": len(domains) == len(set(domains)),
        "all_domains_have_offline_mode": all(route["mode"] in OFFLINE_MODES for route in ROUTES),
        "private_browser_cache_required": False,
        "queued_actions_require_reconciliation": True,
        "unknown_capabilities_fail_closed": True,
        "external_action_permitted_offline": False,
        "human_authority_final": True,
    }
