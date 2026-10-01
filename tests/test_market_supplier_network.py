from __future__ import annotations

from pathlib import Path

import app as app_module
from mission_control import market_supplier_network


def _root() -> Path:
    return Path(app_module.app.root_path)


def test_supplier_network_truth_keeps_oap_front_door_and_execution_locked():
    truth = market_supplier_network.truth_status()

    assert truth["canonical_front_door"] == "OAP Market"
    assert truth["supports_oap_owned_products"] is True
    assert truth["supports_certified_public_merchants"] is True
    assert "tapstitch" in truth["supplier_examples"]
    assert truth["supplier_api_called"] is False
    assert truth["external_order_created"] is False
    assert truth["payment_capture_performed"] is False
    assert truth["money_transfer_performed"] is False
    assert truth["sika_settlement_remains_separate"] is True
    assert truth["provider_adapter_required_for_execution"] is True
    assert truth["human_authority_final"] is True


def test_supplier_store_has_mapping_stop_and_public_projection_without_execution_methods():
    methods = set(dir(market_supplier_network.SupplierNetworkStore))

    assert {"bind_product", "mark_ready", "stop", "owner_bindings", "public_projection"} <= methods

    forbidden = {
        "place_supplier_order",
        "call_supplier_api",
        "capture_payment",
        "transfer_money",
        "dispatch",
        "handoff_to_carrier",
    }
    assert forbidden.isdisjoint(methods)


def test_supplier_schema_is_product_and_seller_scoped():
    source = (
        _root() / "mission_control" / "market_supplier_network.py"
    ).read_text(encoding="utf-8")

    assert "REFERENCES products(id)" in source
    assert "REFERENCES users(id)" in source
    assert "UNIQUE(product_id)" in source
    assert "WHERE id=%s AND seller_id=%s AND active=TRUE" in source
    assert "state='STOPPED'" in source
    assert "state='READY'" in source


def test_public_projection_discloses_only_supplier_label_and_fulfilment_state():
    source = (
        _root() / "mission_control" / "market_supplier_network.py"
    ).read_text(encoding="utf-8")

    assert "manufacturer" in source
    assert "fulfilment_state" in source
    assert "supplier_product_ref" not in source.split("def public_projection", 1)[1].split("STORE =", 1)[0]
    assert "supplier_variant_ref" not in source.split("def public_projection", 1)[1].split("STORE =", 1)[0]
    assert '"external_execution_allowed": False' in source
