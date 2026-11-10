# ruff: noqa: I001
from flask import Flask
import pytest

from mission_control import (
    global_transport_views,
    oap_ride_guardian,
    oap_ride_guardian_outbox,
    oap_ride_private_geometry,
)


def _app():
    app=Flask(__name__)
    app.secret_key="ride-guardian-geometry-test"
    app.register_blueprint(global_transport_views.bp)
    return app


def test_private_route_and_deviation_routes_registered():
    rules={rule.rule for rule in _app().url_map.iter_rules()}
    assert "/transport/ride/bookings/<booking_id>/private-route" in rules
    assert "/transport/ride/bookings/<booking_id>/guardian/deviation" in rules


def test_private_geometry_migration_dry_run_is_bounded():
    state=oap_ride_private_geometry.init_schema(assume_yes=True,dry_run=True)
    assert state["migration"]=="0006_oap_ride_private_geometry"
    assert state["tables"]==1
    assert len(state["checksum"])==64


def test_guardian_outbox_migration_dry_run_is_bounded():
    state=oap_ride_guardian_outbox.init_schema(assume_yes=True,dry_run=True)
    assert state["migration"]=="0007_oap_ride_guardian_outbox"
    assert state["tables"]==1
    assert len(state["checksum"])==64


def test_route_segment_distance_detects_zero_distance():
    geometry={"type":"LineString","coordinates":[[-0.1687,51.4036],[-0.1600,51.4100]]}
    result=oap_ride_guardian._distance_to_route_vertices_m(51.4036,-0.1687,geometry)
    assert result == 0


def test_deviation_rejects_invalid_threshold_before_store_access():
    with pytest.raises(ValueError,match="invalid_deviation_threshold"):
        oap_ride_guardian.analyse_route_deviation(
            booking_id="00000000-0000-0000-0000-000000000001",
            identity_id="00000000-0000-0000-0000-000000000002",
            deviation_threshold_m=5,
        )


def test_route_segment_distance_handles_midpoint_between_vertices():
    geometry={"type":"LineString","coordinates":[[-0.1700,51.4000],[-0.1500,51.4200]]}
    result=oap_ride_guardian._distance_to_route_vertices_m(51.4100,-0.1600,geometry)
    assert result is not None
    assert result < 5
