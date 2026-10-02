from flask import Flask

from mission_control import global_transport_views


def _app():
    app = Flask(__name__)
    app.register_blueprint(global_transport_views.bp)
    return app


def test_rider_driver_my_dashboards_are_registered():
    rules = {rule.rule for rule in _app().url_map.iter_rules()}
    assert "/transport/ride/rider" in rules
    assert "/transport/ride/driver" in rules
    assert "/transport/my" in rules


def test_rider_dashboard_buttons_are_real_links():
    data = _app().test_client().get("/transport/ride/rider").data
    assert b"/movement/workspace#book-title" in data
    assert b"/movement/workspace#bookings-title" in data
    assert b"/movement/workspace#member-matches-title" in data
    assert b"/pay" in data


def test_driver_dashboard_buttons_are_real_links():
    data = _app().test_client().get("/transport/ride/driver").data
    assert b"/movement/workspace#work-title" in data
    assert b"/movement/workspace#assigned-title" in data
    assert b"/pay" in data


def test_my_transport_dashboard_links_to_rider_driver_and_owned_work():
    data = _app().test_client().get("/transport/my").data
    assert b"/transport/ride/rider" in data
    assert b"/transport/ride/driver" in data
    assert b"/movement/workspace#bookings-title" in data
    assert b"/movement/workspace#work-title" in data
