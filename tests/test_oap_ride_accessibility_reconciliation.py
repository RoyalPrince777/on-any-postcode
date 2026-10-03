from flask import Flask
import pytest

from mission_control import (
    global_transport_views,
    oap_ride_driver_accessibility,
    oap_ride_reconciliation,
)


def _app():
    app=Flask(__name__)
    app.secret_key="ride-accessibility-test"
    app.register_blueprint(global_transport_views.bp)
    return app


def test_driver_accessibility_route_registered():
    rules={rule.rule for rule in _app().url_map.iter_rules()}
    assert "/transport/ride/driver/accessibility" in rules


def test_driver_accessibility_migration_dry_run_is_bounded():
    state=oap_ride_driver_accessibility.init_schema(assume_yes=True,dry_run=True)
    assert state["migration"]=="0005_oap_ride_driver_accessibility"
    assert state["tables"]==1
    assert len(state["checksum"])==64


def test_driver_accessibility_rejects_bad_identity_before_store_access():
    with pytest.raises(ValueError,match="invalid_driver_identity_id"):
        oap_ride_driver_accessibility.set_capabilities(
            driver_identity_id="bad",capabilities={}
        )


def test_ride_reconciliation_requires_bound_payment(monkeypatch):
    monkeypatch.setattr(
        "mission_control.oap_ride_reconciliation.oap_ride_payment_bridge.projection",
        lambda booking_id: {"bound":False},
    )
    with pytest.raises(ValueError,match="ride_payment_not_bound"):
        oap_ride_reconciliation.reconcile_ride_payment(
            booking_id="00000000-0000-0000-0000-000000000001",
            journal=object(),provider_id="p",provider_reference="r",
            journal_reference="j",amount="1.00",currency="GBP",
            settlement_status="SETTLED",evidence_hash="x"
        )
