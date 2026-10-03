# ruff: noqa: I001
from flask import Flask
import pytest

from mission_control import global_transport_views, oap_ride_guardian, oap_ride_earnings


def _app():
    app=Flask(__name__)
    app.secret_key="ride-extra-test"
    app.register_blueprint(global_transport_views.bp)
    return app


def test_guardian_and_earnings_routes_registered():
    rules={rule.rule for rule in _app().url_map.iter_rules()}
    assert "/transport/ride/guardian/status" in rules
    assert "/transport/ride/bookings/<booking_id>/guardian" in rules
    assert "/transport/ride/bookings/<booking_id>/guardian/incidents" in rules
    assert "/transport/ride/driver/earnings" in rules


def test_guardian_dry_run_is_bounded_and_no_emergency_claim():
    state=oap_ride_guardian.init_schema(assume_yes=True,dry_run=True)
    assert state["migration"]=="0002_oap_ride_guardian"
    assert state["tables"]==2
    assert len(state["checksum"])==64


def test_guardian_rejects_invalid_identity_before_store_access():
    with pytest.raises(ValueError,match="invalid_booking_id"):
        oap_ride_guardian.set_session(
            booking_id="bad",identity_id="00000000-0000-0000-0000-000000000001",
            enabled=True
        )


def test_driver_earnings_requires_valid_driver_identity():
    with pytest.raises(ValueError,match="invalid_driver_identity_id"):
        oap_ride_earnings.driver_summary(driver_identity_id="bad")
