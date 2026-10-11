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
    assert b'action="/transport/ride/book"' in data
    assert b"/movement/workspace#bookings-title" in data
    assert b"/movement/workspace#member-matches-title" in data
    assert b"/pay" in data


def test_driver_dashboard_buttons_are_real_links():
    data = _app().test_client().get("/transport/ride/driver").data
    assert b"/movement/workspace#work-title" in data
    assert b"/movement/workspace#assigned-title" in data
    assert b"/transport/ride/driver/earnings" in data


def test_my_transport_dashboard_links_to_rider_driver_and_owned_work():
    data = _app().test_client().get("/transport/my").data
    assert b"/transport/ride/rider" in data
    assert b"/transport/ride/driver" in data
    assert b"/movement/workspace#bookings-title" in data
    assert b"/movement/workspace#work-title" in data


def test_rider_primary_journey_action_is_visible_and_existing_route_reused():
    response = _app().test_client().get("/transport/ride/rider")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Where to?" in body
    assert 'name="service" value="ride"' in body
    assert 'name="from"' in body
    assert 'name="to"' in body
    assert 'type="submit"' in body
    assert "Continue to secure booking" in body
    assert "physical dispatch" in body
    assert 'href="/world"' in body


def test_driver_primary_availability_action_reuses_existing_workspace():
    response = _app().test_client().get("/transport/ride/driver")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'class="primary" href="/movement/workspace#work-title"' in body
    assert "Manage availability" in body
    assert "incoming journey proposals" in body


def test_rider_booking_handoff_requires_both_locations():
    body = _app().test_client().get("/transport/ride/rider").get_data(as_text=True)
    assert '<form class="ride-form" action="/transport/ride/book" method="get"' in body
    assert '<input type="hidden" name="service" value="ride">' in body
    assert 'id="ride-pickup" name="from" maxlength="120"' in body
    assert 'id="ride-destination" name="to" maxlength="120"' in body
    assert body.count(" required>") >= 2
    assert "Continue to secure booking" in body


def test_rider_response_is_private_and_not_cached():
    response = _app().test_client().get("/transport/ride/rider")
    assert response.headers["Cache-Control"] == "no-store, private"
    assert b"/transport/ride/rider" in response.data


def test_rider_direct_booking_page_has_governed_submission_contract():
    from mission_control import oap_ride_dashboards
    page = oap_ride_dashboards.RIDE_BOOK_PAGE
    assert 'fetch("/movement/bookings"' in page
    assert '"X-OAP-CSRF":csrf' in page
    assert 'idempotency_key:' in page
    assert 'role="status"' in page
    assert 'credentials:"same-origin"' in page


def test_rider_booking_page_is_login_protected():
    from mission_control import oap_ride_dashboards
    assert hasattr(oap_ride_dashboards.ride_booking_page, "__wrapped__")
    assert "/transport/ride/book" in {rule.rule for rule in _app().url_map.iter_rules()}
