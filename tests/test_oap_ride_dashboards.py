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


def test_my_transport_dashboard_only_selects_role():
    data = _app().test_client().get("/transport/my").data
    assert b"/transport/ride/rider" in data
    assert b"/transport/ride/driver" in data
    assert b"/movement/workspace#bookings-title" not in data
    assert b"/movement/workspace#work-title" not in data


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


def test_authenticated_rider_booking_renders_prefill_and_csrf():
    from unittest.mock import patch

    from mission_control import oap_ride_dashboards
    app = Flask(__name__)
    app.secret_key = "ride-test-key"
    app.register_blueprint(oap_ride_dashboards.bp)
    with patch("mission_control.web_security.current_authenticated_user", return_value={"id": "ride-test-user"}):
        response = app.test_client().get("/transport/ride/book?from=SW1&to=SE15")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store, private"
    assert 'value="SW1"' in body
    assert 'value="SE15"' in body
    assert 'fetch("/movement/bookings"' in body
    assert '"X-OAP-CSRF":csrf' in body


def test_rider_booking_escapes_untrusted_prefill():
    from unittest.mock import patch

    from mission_control import oap_ride_dashboards
    app = Flask(__name__)
    app.secret_key = "ride-test-key"
    app.register_blueprint(oap_ride_dashboards.bp)
    with patch("mission_control.web_security.current_authenticated_user", return_value={"id": "ride-test-user"}):
        response = app.test_client().get("/transport/ride/book?from=%3Cscript%3E&to=SE15")
    assert response.status_code == 200
    assert 'value="&lt;script&gt;"' in response.get_data(as_text=True)


def test_rider_receipt_uses_canonical_movement_booking_id():
    from mission_control import oap_ride_dashboards

    page = oap_ride_dashboards.RIDE_BOOK_PAGE
    assert "data.booking?.booking_id" in page
    assert "data.booking.booking_id" in page
    assert "data.booking?.id" not in page
    assert "requestKey=null" in page


def test_ride_pages_have_separate_pwa_install_identities():
    app = _app()
    for role in ("rider", "driver"):
        path = f"/transport/ride/{role}"
        body = app.test_client().get(path).get_data(as_text=True)
        assert f'rel="manifest" href="{path}/manifest.webmanifest"' in body
        assert f'href="{path}?source=oap-install"' in body
        assert "Install app" in body
        assert "not a signed Android APK" in body
    my_page = app.test_client().get("/transport/my").get_data(as_text=True)
    assert 'rel="manifest" href="/transport/manifest.webmanifest"' in my_page
    assert 'href="/transport"' in my_page


def test_termux_ride_launcher_targets_existing_https_oap_pages():
    from pathlib import Path

    script = Path("scripts/termux_oap_ride.sh").read_text(encoding="utf-8")
    assert 'https://onanypostcode.global' in script
    assert '/transport/ride/rider' in script
    assert '/transport/ride/driver' in script
    assert 'termux-open-url "$url"' in script
    assert 'curl --fail' in script
    assert 'OAP_RIDE_ORIGIN' in script
    assert "dispatch server" in script



def test_rider_retry_key_is_scoped_to_unchanged_journey_details():
    """A corrected pickup/destination must never reuse a prior journey key."""
    from mission_control import oap_ride_dashboards

    page = oap_ride_dashboards.RIDE_BOOK_PAGE
    assert 'const fingerprint=JSON.stringify([pickupValue,destinationValue])' in page
    assert 'if(requestFingerprint!==fingerprint)' in page
    assert 'requestKey="ride-"+crypto.randomUUID();requestFingerprint=fingerprint' in page
    assert 'pickup_query:pickupValue,destination_query:destinationValue' in page
    assert 'requestKey=null;requestFingerprint=null' in page
    assert 'if(pending)return' in page
