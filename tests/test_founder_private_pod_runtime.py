from __future__ import annotations

from pathlib import Path

import pytest

from mission_control import (
    founder_private_pod_mapper,
    founder_private_pod_orders,
)


def _plan(provider_id="prodigi"):
    return {
        "provider_id": provider_id,
        "canonical_order": {
            "quantity": 2,
            "supplier_product_ref": "prodigi-sku-1",
            "supplier_variant_ref": "4011",
            "artwork_reference": "https://example.invalid/artwork.png",
            "garment_type": "t-shirt",
            "placement_options": ["front"],
            "color": "Black",
            "size": "M",
            "destination_country": "GB",
        },
    }


def _address():
    return {
        "name": "Founder",
        "address1": "1 Test Street",
        "city": "London",
        "country_code": "GB",
        "zip": "SE1 1AA",
    }


def test_prodigi_mapping_uses_proven_contract_fields_only():
    payload = founder_private_pod_mapper.map_prodigi(
        plan=_plan("prodigi"),
        delivery_address=_address(),
    )

    assert payload["recipient"]["name"] == "Founder"
    assert payload["recipient"]["address"]["countryCode"] == "GB"
    assert payload["items"] == [
        {
            "sku": "prodigi-sku-1",
            "copies": 2,
            "sizing": "fillPrintArea",
            "assets": [
                {
                    "printArea": "front",
                    "url": "https://example.invalid/artwork.png",
                }
            ],
        }
    ]
    assert payload["shippingMethod"] == "Standard"


def test_printful_mapping_uses_variant_quantity_recipient_and_files():
    payload = founder_private_pod_mapper.map_printful(
        plan=_plan("printful"),
        delivery_address=_address(),
    )

    assert payload["recipient"]["country_code"] == "GB"
    assert payload["items"] == [
        {
            "variant_id": 4011,
            "quantity": 2,
            "files": [{"url": "https://example.invalid/artwork.png"}],
        }
    ]


def test_printful_mapping_rejects_non_numeric_variant():
    plan = _plan("printful")
    plan["canonical_order"]["supplier_variant_ref"] = "not-a-variant-id"

    with pytest.raises(
        founder_private_pod_mapper.FounderPrivatePodMappingError,
        match="printful_variant_reference_invalid",
    ):
        founder_private_pod_mapper.map_printful(
            plan=plan,
            delivery_address=_address(),
        )


def test_tapstitch_mapping_remains_fail_closed():
    with pytest.raises(
        founder_private_pod_mapper.FounderPrivatePodMappingError,
        match="tapstitch_direct_api_contract_unproven",
    ):
        founder_private_pod_mapper.map_provider_payload(
            provider_id="tapstitch",
            plan=_plan("tapstitch"),
            delivery_address=_address(),
        )


def test_mapping_requires_complete_delivery_address():
    with pytest.raises(
        founder_private_pod_mapper.FounderPrivatePodMappingError,
        match="private_delivery_address_incomplete",
    ):
        founder_private_pod_mapper.map_prodigi(
            plan=_plan(),
            delivery_address={"name": "Founder"},
        )


def test_private_order_store_status_keeps_execution_closed():
    status = founder_private_pod_orders.status()

    assert status["durable_provider_choice"] is True
    assert status["durable_provider_payload"] is True
    assert status["public_merchant_access"] is False
    assert status["external_execution_enabled_here"] is False
    assert status["secret_values_persisted"] is False


def test_private_runtime_routes_remain_founder_only_and_snapshot_driven():
    source = (
        Path(founder_private_pod_orders.__file__).parent / "product_core_views.py"
    ).read_text(encoding="utf-8")

    for route in (
        '/market/pod/private/order',
        '/market/pod/private/order/<private_order_id>/execute',
        '/market/pod/private/order/<private_order_id>/readback',
    ):
        position = source.index(route)
        window = source[max(0, position - 220):position + 1500]
        assert "founder_only=True" in window

    execute_start = source.index(
        'def founder_private_pod_order_execute(private_order_id: str):'
    )
    execute_block = source[execute_start:execute_start + 2500]
    assert 'private_order["provider_id"]' in execute_block
    assert 'private_order["provider_payload"]' in execute_block
    assert 'private_order["idempotency_key"]' in execute_block
    assert "payload.get(\"provider_id\")" not in execute_block
    assert "payload.get(\"provider_payload\")" not in execute_block


def test_mapper_status_does_not_claim_provider_execution():
    status = founder_private_pod_mapper.status()

    assert status["prodigi_order_mapping"] is True
    assert status["printful_draft_order_mapping"] is True
    assert status["tapstitch_direct_mapping"] is False
    assert status["provider_call_performed"] is False
    assert status["external_order_created"] is False
