# ruff: noqa: I001
from flask import Flask
import pytest

from mission_control import global_transport_views, oap_ride_commercial


def _app():
    app=Flask(__name__)
    app.secret_key="ride-commercial-test"
    app.register_blueprint(global_transport_views.bp)
    return app


def test_commercial_and_accessibility_routes_registered():
    rules={rule.rule for rule in _app().url_map.iter_rules()}
    assert "/transport/ride/bookings/<booking_id>/accessibility" in rules
    assert "/mission/transport/ride/split-rules" in rules
    assert "/mission/transport/ride/split-rules/active" in rules


def test_commercial_migration_dry_run_is_bounded():
    state=oap_ride_commercial.init_schema(assume_yes=True,dry_run=True)
    assert state["migration"]=="0003_oap_ride_commercial_accessibility"
    assert state["tables"]==2
    assert len(state["checksum"])==64


def test_split_projection_without_rule_does_not_invent_earnings(monkeypatch):
    monkeypatch.setattr(oap_ride_commercial,"active_split",lambda:None)
    result=oap_ride_commercial.project_split(amount_minor=2500)
    assert result["configured"] is False
    assert result["driver_earnings_minor"] is None
    assert result["settlement_performed"] is False


def test_accessibility_rejects_bad_booking_before_store_access():
    with pytest.raises(ValueError,match="invalid_booking_id"):
        oap_ride_commercial.set_accessibility(
            booking_id="bad",
            rider_identity_id="00000000-0000-0000-0000-000000000001",
            preferences={}
        )
