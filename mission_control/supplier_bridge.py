"""OAP Supplier Bridge.

Provider-neutral boundary between OAP Commerce Core and external manufacturers.

This module deliberately does not call provider APIs. It builds a normalized,
private handoff candidate from first-party OAP records and reports the exact
missing conditions that prevent an external manufacturing submission.
"""
from __future__ import annotations

import re
from typing import Any

from . import postgres_db

_PROVIDER_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
_PROVIDER_RECEIPT_STATES = frozenset(
    {"ACCEPTED", "IN_PRODUCTION", "SHIPPED", "DELIVERED", "FAILED", "CANCELLED"}
)

SMI21_CHECKS = (
    "order_exists",
    "order_item_exists",
    "fulfilment_intent_exists",
    "supplier_binding_exists",
    "supplier_ready",
    "design_exists",
    "design_ready",
    "made_to_order",
    "supplier_product_ref_present",
    "supplier_variant_ref_bounded",
    "artwork_reference_present",
    "placements_present",
    "colors_present",
    "sizes_present",
    "delivery_destination_present",
    "payment_capture_proven",
    "provider_connector_authorized",
    "provider_credentials_configured",
    "human_stop_clear",
    "recovery_clear",
    "external_submission_allowed",
)


class SupplierBridgeUnavailable(RuntimeError):
    """Raised when a private Bridge candidate cannot be read safely."""


def _uuid(value: object, code: str) -> str:
    from uuid import UUID

    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(code) from exc


def _provider_slug(value: object) -> str:
    slug = str(value or "").strip().lower()
    if not _PROVIDER_SLUG.fullmatch(slug):
        raise ValueError("invalid_provider_slug")
    return slug


def normalize_provider_receipt(
    *,
    provider_slug: object,
    provider_reference: object,
    state: object,
    tracking_reference: object = "",
) -> dict[str, object]:
    """Normalize an already-received provider receipt without causing execution."""

    slug = _provider_slug(provider_slug)
    reference = str(provider_reference or "").strip()[:240]
    normalized_state = str(state or "").strip().upper()
    tracking = str(tracking_reference or "").strip()[:500]
    if not reference:
        raise ValueError("provider_reference_required")
    if normalized_state not in _PROVIDER_RECEIPT_STATES:
        raise ValueError("invalid_provider_receipt_state")
    return {
        "provider_slug": slug,
        "provider_reference": reference,
        "state": normalized_state,
        "tracking_reference": tracking,
        "external_submission_performed": False,
        "payment_capture_performed": False,
        "money_transfer_performed": False,
        "carrier_dispatch_performed": False,
        "human_authority_final": True,
    }


def handoff_candidate(*, order_id: object) -> dict[str, Any]:
    """Build a private provider-neutral manufacturing candidate.

    The current Commerce schema does not yet own a delivery destination and OAP
    has no authorized provider connector or proven payment capture path. Those
    conditions therefore remain explicit blockers even when supplier/design
    records are READY.
    """

    order = _uuid(order_id, "invalid_order_id")
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT o.order_id,o.state,o.currency,o.subtotal_minor,
                          i.product_id,i.quantity,
                          f.fulfilment_id,f.state,
                          b.supplier_slug,b.supplier_product_ref,
                          b.supplier_variant_ref,b.state,
                          d.garment_type,d.artwork_reference,d.placements,
                          d.colors,d.sizes,d.made_to_order,d.state
                   FROM oap_commerce_orders o
                   LEFT JOIN oap_commerce_order_items i ON i.order_id=o.order_id
                   LEFT JOIN oap_commerce_fulfilment_intents f ON f.order_id=o.order_id
                   LEFT JOIN oap_market_supplier_bindings b ON b.product_id=i.product_id
                   LEFT JOIN oap_market_design_products d ON d.product_id=i.product_id
                   WHERE o.order_id=%s
                   ORDER BY i.created_at ASC
                   LIMIT 1""",
                (order,),
            ).fetchone()
    except Exception as exc:
        raise SupplierBridgeUnavailable("supplier_bridge_read_failed") from exc

    checks = {name: False for name in SMI21_CHECKS}
    if row is None:
        return {
            "order_id": order,
            "bridge_ready": False,
            "checks": checks,
            "block_reasons": ["order_missing"],
            "external_submission_allowed": False,
            "external_submission_performed": False,
            "human_authority_final": True,
        }

    checks["order_exists"] = True
    checks["order_item_exists"] = row[4] is not None
    checks["fulfilment_intent_exists"] = row[6] is not None
    checks["supplier_binding_exists"] = row[8] is not None
    checks["supplier_ready"] = str(row[11] or "") == "READY"
    checks["design_exists"] = row[12] is not None
    checks["design_ready"] = str(row[18] or "") == "READY"
    checks["made_to_order"] = bool(row[17])
    checks["supplier_product_ref_present"] = bool(str(row[9] or "").strip())
    checks["supplier_variant_ref_bounded"] = len(str(row[10] or "")) <= 240
    checks["artwork_reference_present"] = bool(str(row[13] or "").strip())
    checks["placements_present"] = bool(list(row[14] or []))
    checks["colors_present"] = bool(list(row[15] or []))
    checks["sizes_present"] = bool(list(row[16] or []))

    # Deliberate fail-closed boundaries until first-party support is added.
    checks["delivery_destination_present"] = False
    checks["payment_capture_proven"] = False
    checks["provider_connector_authorized"] = False
    checks["provider_credentials_configured"] = False
    checks["human_stop_clear"] = True
    checks["recovery_clear"] = True
    checks["external_submission_allowed"] = False

    reasons = [name for name, passed in checks.items() if not passed]
    return {
        "order_id": order,
        "product_id": str(row[4]) if row[4] else None,
        "fulfilment_id": str(row[6]) if row[6] else None,
        "provider_slug": str(row[8] or ""),
        "supplier_product_ref": str(row[9] or ""),
        "supplier_variant_ref": str(row[10] or ""),
        "quantity": int(row[5] or 0),
        "garment_type": str(row[12] or ""),
        "artwork_reference": str(row[13] or ""),
        "placements": list(row[14] or []),
        "colors": list(row[15] or []),
        "sizes": list(row[16] or []),
        "bridge_ready": all(checks.values()),
        "checks": checks,
        "block_reasons": reasons,
        "external_submission_allowed": False,
        "external_submission_performed": False,
        "payment_capture_performed": False,
        "money_transfer_performed": False,
        "carrier_dispatch_performed": False,
        "human_authority_final": True,
    }


def truth_status() -> dict[str, object]:
    """Static truth boundaries for the first-party Bridge contract."""

    return {
        "component": "OAP Supplier Bridge",
        "provider_neutral_contract": True,
        "smi21_check_count": len(SMI21_CHECKS),
        "normalized_provider_receipts": True,
        "external_submission_enabled": False,
        "payment_capture_enabled": False,
        "money_transfer_enabled": False,
        "carrier_dispatch_enabled": False,
        "delivery_destination_supported": False,
        "provider_connector_required": True,
        "human_authority_final": True,
    }
