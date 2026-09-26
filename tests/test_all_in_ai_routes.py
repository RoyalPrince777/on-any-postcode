from flask import Flask

from mission_control import all_in_ai_views


def test_all_in_ai_route_registers_founder_command_surface():
    app = Flask(__name__)
    app.secret_key = "test"
    app.register_blueprint(all_in_ai_views.bp, url_prefix="/mission")
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/mission/all-in-ai" in rules
    assert "/mission/all-in-ai/app" in rules
    assert "/mission/all-in-ai/mission" in rules
    assert "/mission/all-in-ai/mission/<mission_id>" in rules
    assert "/mission/all-in-ai/mission/<mission_id>/stop" in rules
    assert "/mission/all-in-ai/mission/<mission_id>/recover" in rules


def test_all_in_ai_route_is_not_public():
    app = Flask(__name__)
    app.secret_key = "test"
    app.register_blueprint(all_in_ai_views.bp, url_prefix="/mission")
    response = app.test_client().get("/mission/all-in-ai")
    assert response.status_code in {401, 403}


def test_all_in_ai_mission_route_is_not_public():
    app = Flask(__name__)
    app.secret_key = "test"
    app.register_blueprint(all_in_ai_views.bp, url_prefix="/mission")
    response = app.test_client().post(
        "/mission/all-in-ai/mission",
        json={"mission": "test"},
    )
    assert response.status_code in {401, 403}


def test_all_in_ai_lifecycle_routes_are_not_public():
    app = Flask(__name__)
    app.secret_key = "test"
    app.register_blueprint(all_in_ai_views.bp, url_prefix="/mission")
    mission = "00000000-0000-0000-0000-000000000002"
    client = app.test_client()
    assert client.get(f"/mission/all-in-ai/mission/{mission}").status_code in {401, 403}
    assert client.post(
        f"/mission/all-in-ai/mission/{mission}/stop",
        json={"expected_previous_hash": "a" * 64},
    ).status_code in {401, 403}
    assert client.post(
        f"/mission/all-in-ai/mission/{mission}/recover",
        json={"expected_previous_hash": "b" * 64},
    ).status_code in {401, 403}


def test_all_in_ai_app_route_is_not_public():
    app = Flask(__name__)
    app.secret_key = "test"
    app.register_blueprint(all_in_ai_views.bp, url_prefix="/mission")
    response = app.test_client().get("/mission/all-in-ai/app")
    assert response.status_code in {302, 401, 403}
