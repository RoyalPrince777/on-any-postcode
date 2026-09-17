"""Passive proof adapter for Market, Media and Distribution monitor lanes.

This module only exposes coarse first-party readiness evidence. It does not read
identity-scoped storefront, order, release, playlist or rights records and it
never performs payment, publishing, fulfilment, playback or external delivery.
"""
from __future__ import annotations

from typing import Any

from . import distribution_intelligence, product_cores


def observations(generated_at: str) -> tuple[dict[str, Any], ...]:
    try:
        platform = product_cores.platform_status()
    except Exception:  # noqa: BLE001 - monitor must fail closed.
        platform = {}
    try:
        distribution = distribution_intelligence.status()
    except Exception:  # noqa: BLE001 - monitor must fail closed.
        distribution = {}

    schema_ready = bool(platform.get("ready") or platform.get("schema_ready"))
    legacy_market_preserved = bool(platform.get("legacy_market_preserved"))
    blocked_external_actions = tuple(platform.get("blocked_external_actions") or ())
    platform_seen = bool(platform)
    distribution_contract_ready = bool(distribution.get("ready"))
    external_distribution_locked = (
        str(distribution.get("external_distribution_state") or "")
        == "locked_until_authenticated_adapter_and_receipt"
    )

    common_source_timestamp = generated_at if (platform_seen or distribution) else None

    market = {
        "id": "oap_market_runtime",
        "name": "OAP Market Runtime Evidence",
        "source": "mission_control.product_cores.platform_status",
        "source_timestamp": common_source_timestamp,
        "observed_at": generated_at,
        "freshness": "checked_now_identity_activity_unproven" if schema_ready else "unseen",
        "freshness_window_seconds": 0,
        "evidence": {
            "schema_ready": schema_ready,
            "legacy_market_preserved": legacy_market_preserved,
            "storefront_activity_proven": False,
            "product_activity_proven": False,
            "order_activity_proven": False,
            "payment_capture_performed": False,
            "money_transfer_performed": False,
            "external_fulfilment_performed": False,
            "blocked_external_actions": blocked_external_actions,
            "identity_scoped_data_read": False,
            "read_only": True,
        },
        "proof_state": "partial_proof" if schema_ready else "proof_required",
        "external_authority": False,
    }

    media = {
        "id": "oap_media_runtime",
        "name": "OAP Media Runtime Evidence",
        "source": "mission_control.product_cores.platform_status",
        "source_timestamp": common_source_timestamp,
        "observed_at": generated_at,
        "freshness": "checked_now_identity_activity_unproven" if schema_ready else "unseen",
        "freshness_window_seconds": 0,
        "evidence": {
            "schema_ready": schema_ready,
            "release_activity_proven": False,
            "playlist_activity_proven": False,
            "rights_activity_proven": False,
            "licensed_audio_delivery": False,
            "royalty_payout": False,
            "external_distribution": False,
            "identity_scoped_data_read": False,
            "read_only": True,
        },
        "proof_state": "partial_proof" if schema_ready else "proof_required",
        "external_authority": False,
    }

    distribution_observation = {
        "id": "oap_distribution_runtime",
        "name": "OAP Distribution Runtime Evidence",
        "source": "mission_control.distribution_intelligence.status",
        "source_timestamp": common_source_timestamp,
        "observed_at": generated_at,
        "freshness": (
            "checked_now_release_activity_unproven"
            if distribution_contract_ready
            else "unseen"
        ),
        "freshness_window_seconds": 0,
        "evidence": {
            "contract_ready": distribution_contract_ready,
            "rights_proof_required": bool(distribution.get("rights_proof_required", True)),
            "external_distribution_locked": external_distribution_locked,
            "publishing_authority_granted": bool(
                distribution.get("publishing_authority_granted", False)
            ),
            "payment_authority_granted": bool(
                distribution.get("payment_authority_granted", False)
            ),
            "external_execution_enabled": bool(
                distribution.get("external_execution_enabled", False)
            ),
            "release_activity_proven": False,
            "rights_receipt_proven": False,
            "external_delivery_receipt_proven": False,
            "identity_scoped_data_read": False,
            "read_only": True,
        },
        "proof_state": (
            "partial_proof" if distribution_contract_ready else "proof_required"
        ),
        "external_authority": False,
    }

    return market, media, distribution_observation
