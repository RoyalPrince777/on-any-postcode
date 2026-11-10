"""Founder-private POD commerce coordination for OAP Market.

This layer composes OAP-owned product truth, supplier routing, canonical order
mapping, reconciliation, recovery hints, and private analytics without opening
public merchant execution or submitting an external manufacturer order.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from . import pod_provider_registry

CANONICAL_PROVIDER_STATES = {
    "DRAFT": "DRAFT",
    "CREATED": "ORDER_CREATED",
    "PENDING": "ORDER_CREATED",
    "ACCEPTED": "ORDER_CREATED",
    "INPROGRESS": "IN_PRODUCTION",
    "IN_PROGRESS": "IN_PRODUCTION",
    "INPRODUCTION": "IN_PRODUCTION",
    "IN_PRODUCTION": "IN_PRODUCTION",
    "SHIPPED": "SHIPPED",
    "FULFILLED": "SHIPPED",
    "COMPLETE": "DELIVERED",
    "COMPLETED": "DELIVERED",
    "DELIVERED": "DELIVERED",
    "FAILED": "RECOVERY_REQUIRED",
    "ERROR": "RECOVERY_REQUIRED",
    "CANCELLED": "CANCELLED",
    "CANCELED": "CANCELLED",
}


class FounderPrivateCommerceError(RuntimeError):
    """Safe Founder-private commerce error."""


def _clean(value: object, *, limit: int) -> str:
    return str(value or "").strip()[:limit]


def _positive_quantity(value: object) -> int:
    try:
        quantity = int(value)
    except (TypeError, ValueError) as exc:
        raise FounderPrivateCommerceError("private_quantity_invalid") from exc
    if quantity < 1 or quantity > 100:
        raise FounderPrivateCommerceError("private_quantity_invalid")
    return quantity


def _select_option(value: object, allowed: object, code: str) -> str:
    selected = _clean(value, limit=80)
    values = [str(item) for item in allowed] if isinstance(allowed, list) else []
    if not selected or selected not in values:
        raise FounderPrivateCommerceError(code)
    return selected


def resolve_private_provider(product: dict[str, Any], requested: object = None) -> str:
    """Resolve provider from an explicit private choice or the product binding."""

    explicit = _clean(requested, limit=64).lower()
    if explicit:
        return pod_provider_registry.resolve_provider_id(explicit)

    candidates = (
        _clean(product.get("supplier_slug"), limit=64).lower(),
        _clean(product.get("supplier_label"), limit=64).lower(),
    )
    for candidate in candidates:
        if candidate in pod_provider_registry.SUPPORTED_PROVIDERS:
            return candidate
    raise FounderPrivateCommerceError("private_provider_binding_required")


def private_fulfilment_plan(
    *,
    product: dict[str, Any],
    quantity: object,
    provider_id: object = None,
    color: object,
    size: object,
    destination_country: object,
) -> dict[str, object]:
    """Build a canonical private order envelope without provider execution."""

    if product.get("private_owner_view") is not True:
        raise FounderPrivateCommerceError("private_owner_product_required")
    if str(product.get("supplier_state") or "") != "READY":
        raise FounderPrivateCommerceError("private_supplier_not_ready")
    if str(product.get("design_state") or "") != "READY":
        raise FounderPrivateCommerceError("private_design_not_ready")

    provider = resolve_private_provider(product, provider_id)
    if provider == "tapstitch":
        direct_contract = pod_provider_registry.status()["providers"]["tapstitch"].get(
            "direct_order_api_contract_proven"
        )
        if direct_contract is not True:
            raise FounderPrivateCommerceError("tapstitch_direct_api_contract_unproven")

    product_id = _clean(product.get("product_id"), limit=80)
    supplier_product_ref = _clean(product.get("supplier_product_ref"), limit=240)
    supplier_variant_ref = _clean(product.get("supplier_variant_ref"), limit=240)
    artwork_reference = _clean(product.get("artwork_reference"), limit=500)
    country = _clean(destination_country, limit=2).upper()
    if not all((product_id, supplier_product_ref, artwork_reference)):
        raise FounderPrivateCommerceError("private_product_mapping_incomplete")
    if len(country) != 2 or not country.isalpha():
        raise FounderPrivateCommerceError("private_destination_country_invalid")

    chosen_color = _select_option(
        color, product.get("colors"), "private_color_not_available"
    )
    chosen_size = _select_option(
        size, product.get("sizes"), "private_size_not_available"
    )
    qty = _positive_quantity(quantity)

    return {
        "scope": "founder_private",
        "product_id": product_id,
        "provider_id": provider,
        "canonical_order": {
            "quantity": qty,
            "supplier_product_ref": supplier_product_ref,
            "supplier_variant_ref": supplier_variant_ref,
            "artwork_reference": artwork_reference,
            "garment_type": _clean(product.get("garment_type"), limit=120),
            "placement_options": list(product.get("placements") or []),
            "color": chosen_color,
            "size": chosen_size,
            "destination_country": country,
        },
        "private_plan_ready": True,
        "public_listing_required": False,
        "public_merchant_access": False,
        "provider_payload_mapping_ready": False,
        "provider_execution_allowed": False,
        "external_order_created": False,
        "payment_capture_performed": False,
        "money_transfer_performed": False,
        "recovery_required": False,
        "human_authority_final": True,
    }


def reconcile_provider_state(
    *, provider_id: object, provider_state: object
) -> dict[str, object]:
    """Normalize provider evidence into OAP state without inventing completion."""

    provider = pod_provider_registry.resolve_provider_id(provider_id)
    raw_state = _clean(provider_state, limit=40).upper().replace(" ", "_")
    if not raw_state:
        raise FounderPrivateCommerceError("provider_state_required")
    canonical = CANONICAL_PROVIDER_STATES.get(raw_state, "REVIEW_REQUIRED")
    recovery_required = canonical in {"RECOVERY_REQUIRED", "REVIEW_REQUIRED"}
    return {
        "scope": "founder_private",
        "provider_id": provider,
        "provider_state": raw_state,
        "canonical_state": canonical,
        "recovery_required": recovery_required,
        "automatic_public_effect": False,
        "automatic_refund_performed": False,
        "automatic_reprint_performed": False,
        "human_authority_final": True,
    }


def private_catalogue_analytics(products: list[dict[str, Any]]) -> dict[str, object]:
    """Aggregate only owner-private catalogue state; never expose customer data."""

    supplier_states = Counter(str(row.get("supplier_state") or "UNKNOWN") for row in products)
    design_states = Counter(str(row.get("design_state") or "UNKNOWN") for row in products)
    private_ready = sum(
        1
        for row in products
        if str(row.get("supplier_state") or "") == "READY"
        and str(row.get("design_state") or "") == "READY"
    )
    public_active = sum(1 for row in products if row.get("public_listing_active") is True)
    return {
        "scope": "founder_private",
        "product_count": len(products),
        "private_ready_count": private_ready,
        "public_active_count": public_active,
        "private_only_count": len(products) - public_active,
        "supplier_states": dict(sorted(supplier_states.items())),
        "design_states": dict(sorted(design_states.items())),
        "customer_data_included": False,
        "provider_secrets_included": False,
        "external_execution_performed": False,
        "human_authority_final": True,
    }


def status() -> dict[str, object]:
    return {
        "system": "OAP Founder Private Commerce",
        "founder_private_only": True,
        "canonical_order_mapping": True,
        "private_supplier_routing": True,
        "provider_state_reconciliation": True,
        "private_catalogue_analytics": True,
        "public_merchant_access": False,
        "public_seller_launch": False,
        "provider_payload_mapping_ready": False,
        "external_execution_enabled_here": False,
        "automatic_supplier_failover": False,
        "automatic_refund_or_reprint": False,
        "secret_values_exposed": False,
        "human_authority_final": True,
    }
