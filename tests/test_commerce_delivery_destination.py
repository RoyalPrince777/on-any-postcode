from __future__ import annotations

import pytest

from mission_control import commerce_delivery_destination as destination


def test_destination_schema_is_order_owned_and_checksum_gated():
    sql = "\n".join(destination.DELIVERY_DESTINATION_SCHEMA_STATEMENTS)

    assert "oap_commerce_delivery_destinations" in sql
    assert "REFERENCES oap_commerce_orders(order_id)" in sql
    assert "buyer_identity_id UUID NOT NULL REFERENCES users(id)" in sql
    assert "order_id UUID NOT NULL UNIQUE" in sql
    assert len(destination.DELIVERY_DESTINATION_MIGRATION_CHECKSUM) == 64


def test_normalize_destination_bounds_and_uppercases_country():
    value = destination.normalize_destination(
        recipient_name="  Jane   Doe ",
        address_line1=" 1 High Street ",
        address_line2="",
        locality=" London ",
        region=" Greater London ",
        postal_code=" SW1A 1AA ",
        country_code="gb",
        delivery_instructions=" leave with concierge ",
    )

    assert value == {
        "recipient_name": "Jane Doe",
        "address_line1": "1 High Street",
        "address_line2": None,
        "locality": "London",
        "region": "Greater London",
        "postal_code": "SW1A 1AA",
        "country_code": "GB",
        "delivery_instructions": "leave with concierge",
    }


@pytest.mark.parametrize("country", ["", "G", "GBR", "1B", "G1"])
def test_normalize_destination_rejects_invalid_country(country):
    with pytest.raises(ValueError, match="invalid_country_code"):
        destination.normalize_destination(
            recipient_name="Jane Doe",
            address_line1="1 High Street",
            locality="London",
            postal_code="SW1A 1AA",
            country_code=country,
        )


def test_status_never_claims_external_execution():
    status = destination.status()

    assert status["one_destination_per_order"] is True
    assert status["buyer_ownership_enforced"] is True
    assert status["provider_submission_performed"] is False
    assert status["payment_capture_performed"] is False
    assert status["carrier_dispatch_performed"] is False
    assert status["human_authority_final"] is True
