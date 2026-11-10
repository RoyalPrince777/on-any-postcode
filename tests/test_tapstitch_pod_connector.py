from __future__ import annotations

import pytest

from mission_control import market_supplier_network, tapstitch_pod_connector


def test_tapstitch_profile_is_supported_but_direct_execution_is_locked():
    status = tapstitch_pod_connector.status()

    assert status["provider_id"] == "tapstitch"
    assert status["manufacturer_route_supported"] is True
    assert status["product_mapping_supported"] is True
    assert status["store_integration_supported"] is True
    assert status["direct_order_api_contract_proven"] is False
    assert status["external_order_execution_enabled"] is False
    assert status["provider_credentials_configured"] is False
    assert status["signed_webhook_contract_proven"] is False
    assert status["manual_or_store_link_required"] is True
    assert status["secret_values_exposed"] is False


def test_tapstitch_execution_fails_closed_until_api_contract_is_proven():
    with pytest.raises(RuntimeError, match="tapstitch_direct_api_contract_unproven"):
        tapstitch_pod_connector.assert_external_execution_allowed()


def test_supplier_network_exposes_tapstitch_truth_profile():
    truth = market_supplier_network.truth_status()

    assert truth["supplier_profiles"]["tapstitch"]["provider_id"] == "tapstitch"
    assert (
        truth["supplier_profiles"]["tapstitch"]["external_order_execution_enabled"]
        is False
    )
