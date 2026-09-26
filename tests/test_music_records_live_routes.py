from flask import Flask

from mission_control import product_core_views


def test_records_and_live_music_routes_are_registered_with_expected_methods():
    app = Flask(__name__)
    app.register_blueprint(product_core_views.bp, url_prefix="/mission/organs")
    rules = {rule.rule: rule.methods for rule in app.url_map.iter_rules()}
    expected = {
        "/mission/organs/records": {"GET", "HEAD", "OPTIONS"},
        "/mission/organs/records/masters": {"POST", "OPTIONS"},
        "/mission/organs/records/credits": {"POST", "OPTIONS"},
        "/mission/organs/records/receipts": {"POST", "OPTIONS"},
        "/mission/organs/live-music": {"GET", "HEAD", "OPTIONS"},
        "/mission/organs/live-music/sessions": {"POST", "OPTIONS"},
        "/mission/organs/live-music/sessions/<session_id>/stop": {"POST", "OPTIONS"},
        "/mission/organs/live-music/sessions/<session_id>/archive": {"POST", "OPTIONS"},
    }
    for path, methods in expected.items():
        assert rules[path] == methods


def test_records_and_live_writes_use_shared_csrf_write_handler(monkeypatch):
    app = Flask(__name__)
    monkeypatch.setattr(product_core_views, "_write_allowed", lambda: False)
    with app.test_request_context("/", method="POST", json={}):
        records_response = product_core_views.create_records_master.__wrapped__()
        live_response = product_core_views.create_live_music_session.__wrapped__()
    assert records_response.status_code == 403
    assert live_response.status_code == 403
