from flask import Flask
import pytest

from mission_control import (
    global_transport_views,
    oap_ride_guardian,
    oap_ride_payment_bridge,
)


def _app():
    app=Flask(__name__)
    app.secret_key="ride-payment-guardian-test"
    app.register_blueprint(global_transport_views.bp)
    return app


def test_payment_bridge_and_guardian_analysis_routes_registered():
    rules={rule.rule for rule in _app().url_map.iter_rules()}
    assert "/transport/ride/bookings/<booking_id>/sika-payment" in rules
    assert "/transport/ride/bookings/<booking_id>/guardian/analyse" in rules


def test_payment_bridge_migration_dry_run_is_bounded():
    state=oap_ride_payment_bridge.init_schema(assume_yes=True,dry_run=True)
    assert state["migration"]=="0004_oap_ride_payment_bridge"
    assert state["tables"]==1
    assert len(state["checksum"])==64


def test_payment_bridge_rejects_bad_booking_before_store_access():
    with pytest.raises(ValueError,match="invalid_booking_id"):
        oap_ride_payment_bridge.bind(
            booking_id="bad",
            rider_identity_id="00000000-0000-0000-0000-000000000001",
            payment_id="pay-1",
        )


def test_guardian_distance_is_reasonable():
    distance=oap_ride_guardian._distance_m(51.4036,-0.1687,51.4036,-0.1687)
    assert distance == 0


def test_guardian_rejects_invalid_threshold_before_store_access():
    with pytest.raises(ValueError,match="invalid_guardian_threshold"):
        oap_ride_guardian.analyse_tracking(
            booking_id="00000000-0000-0000-0000-000000000001",
            identity_id="00000000-0000-0000-0000-000000000002",
            stop_minutes=0,
        )
