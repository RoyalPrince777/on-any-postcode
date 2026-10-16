from flask import Flask

from mission_control import tv_views


def test_tv_routes_register():
    app = Flask(__name__, template_folder="../mission_control/templates")
    app.secret_key = "test"
    app.register_blueprint(tv_views.bp)
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/tv" in rules
    assert "/tv/status" in rules
    assert "/mission/tv/command-center" in rules


def test_public_tv_status_is_truth_mode_and_not_fake_green():
    app = Flask(__name__, template_folder="../mission_control/templates")
    app.secret_key = "test"
    app.register_blueprint(tv_views.bp)
    client = app.test_client()
    response = client.get("/tv/status")
    assert response.status_code == 200
    data = response.get_json()
    assert data["truth_mode"] is True
    assert data["red_team"]["green"] is False
    assert data["live_broadcast_claimed"] is False
    assert data["external_distribution_claimed"] is False
