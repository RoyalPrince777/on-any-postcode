from flask import Flask
import pytest

from mission_control import global_transport_views, oap_ride_runtime


def _app():
    app = Flask(__name__)
    app.secret_key = "ride-test"
    app.register_blueprint(global_transport_views.bp)
    return app


def test_ride_lifecycle_routes_are_registered():
    rules = {rule.rule for rule in _app().url_map.iter_rules()}
    expected = {
        "/transport/ride/runtime/schema",
        "/transport/ride/bookings/<booking_id>/journey-code",
        "/transport/ride/bookings/<booking_id>/start",
        "/transport/ride/bookings/<booking_id>/complete",
        "/transport/ride/bookings/<booking_id>/receipt",
        "/transport/ride/bookings/<booking_id>/feedback",
        "/transport/ride/current",
    }
    assert expected <= rules


def test_ride_runtime_migration_dry_run_is_bounded():
    state = oap_ride_runtime.init_schema(assume_yes=True, dry_run=True)
    assert state["dry_run"] is True
    assert state["migration"] == "0001_oap_ride_runtime"
    assert state["tables"] == 3
    assert len(state["checksum"]) == 64


def test_start_rejects_bad_journey_code_before_store_access():
    with pytest.raises(ValueError, match="invalid_journey_code"):
        oap_ride_runtime.verify_and_start(
            booking_id="00000000-0000-0000-0000-000000000001",
            driver_identity_id="00000000-0000-0000-0000-000000000002",
            journey_code="12",
        )


def test_feedback_rejects_invalid_rating_before_store_access():
    with pytest.raises(ValueError, match="invalid_rating"):
        oap_ride_runtime.leave_feedback(
            booking_id="00000000-0000-0000-0000-000000000001",
            author_identity_id="00000000-0000-0000-0000-000000000002",
            rating=9,
        )
