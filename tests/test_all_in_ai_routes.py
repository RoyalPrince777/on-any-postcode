from flask import Flask

from mission_control import all_in_ai_views


def test_all_in_ai_route_registers_founder_command_surface():
    app = Flask(__name__)
    app.secret_key = "test"
    app.register_blueprint(all_in_ai_views.bp, url_prefix="/mission")
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/mission/all-in-ai" in rules


def test_all_in_ai_route_is_not_public():
    app = Flask(__name__)
    app.secret_key = "test"
    app.register_blueprint(all_in_ai_views.bp, url_prefix="/mission")
    response = app.test_client().get("/mission/all-in-ai")
    assert response.status_code in {401, 403}
