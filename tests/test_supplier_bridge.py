from __future__ import annotations

from pathlib import Path

import pytest

from mission_control import supplier_bridge


def test_supplier_bridge_has_exact_smi21_truth_checks():
    assert len(supplier_bridge.SMI21_CHECKS) == 21
    assert len(set(supplier_bridge.SMI21_CHECKS)) == 21
    assert supplier_bridge.SMI21_CHECKS[-1] == "external_submission_allowed"


def test_supplier_bridge_truth_status_fails_closed_on_external_execution():
    status = supplier_bridge.truth_status()

    assert status["component"] == "OAP Supplier Bridge"
    assert status["provider_neutral_contract"] is True
    assert status["smi21_check_count"] == 21
    assert status["external_submission_enabled"] is False
    assert status["payment_capture_enabled"] is False
    assert status["money_transfer_enabled"] is False
    assert status["carrier_dispatch_enabled"] is False
    assert status["delivery_destination_supported"] is True
    assert status["provider_connector_required"] is True


def test_provider_receipt_normalization_never_performs_execution():
    receipt = supplier_bridge.normalize_provider_receipt(
        provider_slug="tapstitch",
        provider_reference="provider-order-123",
        state="shipped",
        tracking_reference="tracking-123",
    )

    assert receipt["provider_slug"] == "tapstitch"
    assert receipt["state"] == "SHIPPED"
    assert receipt["external_submission_performed"] is False
    assert receipt["payment_capture_performed"] is False
    assert receipt["money_transfer_performed"] is False
    assert receipt["carrier_dispatch_performed"] is False


@pytest.mark.parametrize("state", ["", "READY", "SUBMITTED", "UNKNOWN"])
def test_provider_receipt_rejects_non_receipt_states(state):
    with pytest.raises(ValueError, match="invalid_provider_receipt_state"):
        supplier_bridge.normalize_provider_receipt(
            provider_slug="tapstitch",
            provider_reference="ref",
            state=state,
        )


def test_supplier_bridge_has_no_network_client_or_secret_access():
    source = (
        Path(__file__).resolve().parents[1]
        / "mission_control"
        / "supplier_bridge.py"
    ).read_text(encoding="utf-8")

    for forbidden in (
        "requests.",
        "httpx.",
        "urllib.request",
        "OPENAI_API_KEY",
        "RENDER_API_KEY",
        "TAPSTITCH_API_KEY",
    ):
        assert forbidden not in source
