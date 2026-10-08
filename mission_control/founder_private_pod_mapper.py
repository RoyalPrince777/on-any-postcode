"""Provider-specific payload mapping for Founder-private POD orders.

Only fields grounded in the proven Prodigi and Printful order contracts are
emitted. Mapping never calls a provider and never enables fulfilment.
"""
from __future__ import annotations

from typing import Any


class FounderPrivatePodMappingError(RuntimeError):
    """Safe mapping error."""


def _clean(value: object, *, limit: int) -> str:
    return str(value or "").strip()[:limit]


def _address(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        raise FounderPrivatePodMappingError("private_delivery_address_required")
    required = ("name", "address1", "city", "country_code", "zip")
    result = {key: _clean(value.get(key), limit=160) for key in required}
    if not all(result.values()):
        raise FounderPrivatePodMappingError("private_delivery_address_incomplete")
    country = result["country_code"].upper()
    if len(country) != 2 or not country.isalpha():
        raise FounderPrivatePodMappingError("private_delivery_country_invalid")
    result["country_code"] = country
    for key in ("address2", "state_code", "phone", "email"):
        optional = _clean(value.get(key), limit=160)
        if optional:
            result[key] = optional
    return result


def _canonical(plan: object) -> dict[str, Any]:
    if not isinstance(plan, dict):
        raise FounderPrivatePodMappingError("private_plan_required")
    canonical = plan.get("canonical_order")
    if not isinstance(canonical, dict):
        raise FounderPrivatePodMappingError("private_canonical_order_required")
    return dict(canonical)


def map_prodigi(*, plan: object, delivery_address: object) -> dict[str, object]:
    canonical = _canonical(plan)
    address = _address(delivery_address)
    sku = _clean(canonical.get("supplier_product_ref"), limit=240)
    artwork = _clean(canonical.get("artwork_reference"), limit=500)
    if not sku or not artwork:
        raise FounderPrivatePodMappingError("prodigi_private_mapping_incomplete")
    quantity = int(canonical.get("quantity") or 0)
    if quantity < 1:
        raise FounderPrivatePodMappingError("private_quantity_invalid")

    asset = {
        "printArea": _clean(
            (canonical.get("placement_options") or ["default"])[0], limit=80
        )
        or "default",
        "url": artwork,
    }
    item: dict[str, object] = {
        "sku": sku,
        "copies": quantity,
        "sizing": "fillPrintArea",
        "assets": [asset],
    }
    return {
        "recipient": {
            "name": address["name"],
            "address": {
                "line1": address["address1"],
                **({"line2": address["address2"]} if address.get("address2") else {}),
                "postalOrZipCode": address["zip"],
                "townOrCity": address["city"],
                **({"stateOrCounty": address["state_code"]} if address.get("state_code") else {}),
                "countryCode": address["country_code"],
            },
        },
        "items": [item],
        "shippingMethod": "Standard",
    }


def map_printful(*, plan: object, delivery_address: object) -> dict[str, object]:
    canonical = _canonical(plan)
    address = _address(delivery_address)
    variant_ref = _clean(canonical.get("supplier_variant_ref"), limit=240)
    artwork = _clean(canonical.get("artwork_reference"), limit=500)
    if not variant_ref:
        raise FounderPrivatePodMappingError("printful_variant_reference_required")
    try:
        variant_id = int(variant_ref)
    except ValueError as exc:
        raise FounderPrivatePodMappingError("printful_variant_reference_invalid") from exc
    quantity = int(canonical.get("quantity") or 0)
    if quantity < 1:
        raise FounderPrivatePodMappingError("private_quantity_invalid")

    item: dict[str, object] = {
        "variant_id": variant_id,
        "quantity": quantity,
    }
    if artwork:
        item["files"] = [{"url": artwork}]

    recipient: dict[str, str] = {
        "name": address["name"],
        "address1": address["address1"],
        "city": address["city"],
        "country_code": address["country_code"],
        "zip": address["zip"],
    }
    for key in ("address2", "state_code", "phone", "email"):
        if address.get(key):
            recipient[key] = address[key]

    return {"recipient": recipient, "items": [item]}


def map_provider_payload(
    *, provider_id: object, plan: object, delivery_address: object
) -> dict[str, object]:
    provider = _clean(provider_id, limit=40).lower()
    if provider == "prodigi":
        return map_prodigi(plan=plan, delivery_address=delivery_address)
    if provider == "printful":
        return map_printful(plan=plan, delivery_address=delivery_address)
    if provider == "tapstitch":
        raise FounderPrivatePodMappingError("tapstitch_direct_api_contract_unproven")
    raise FounderPrivatePodMappingError("private_provider_not_supported")


def status() -> dict[str, object]:
    return {
        "system": "OAP Founder Private POD Mapper",
        "prodigi_order_mapping": True,
        "printful_draft_order_mapping": True,
        "tapstitch_direct_mapping": False,
        "public_merchant_access": False,
        "provider_call_performed": False,
        "external_order_created": False,
        "human_authority_final": True,
    }
