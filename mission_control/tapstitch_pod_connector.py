"""Tapstitch provider profile for OAP Supplier Bridge.

This profile records the currently verified integration boundary only.
Tapstitch is supported as a manufacturer/product-mapping route, but OAP does
not claim a direct order API contract until authoritative provider evidence
proves one.
"""
from __future__ import annotations


def status() -> dict[str, object]:
    return {
        "provider_id": "tapstitch",
        "display_name": "Tapstitch",
        "manufacturer_route_supported": True,
        "product_mapping_supported": True,
        "store_integration_supported": True,
        "direct_order_api_contract_proven": False,
        "external_order_execution_enabled": False,
        "provider_credentials_configured": False,
        "signed_webhook_contract_proven": False,
        "manual_or_store_link_required": True,
        "secret_values_exposed": False,
        "human_authority_final": True,
    }


def assert_external_execution_allowed() -> None:
    """Fail closed until a direct Tapstitch API contract is proven."""

    raise RuntimeError("tapstitch_direct_api_contract_unproven")
