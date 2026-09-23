"""Raffles private Command Centre route and button-contract regressions."""
from pathlib import Path

from flask import Flask

from mission_control import raffles_command_views as views

ROOT = Path(__file__).resolve().parents[1]


def app():
    flask_app = Flask(__name__)
    flask_app.secret_key = "offline-test-only"
    flask_app.register_blueprint(views.bp)
    return flask_app


def test_review_returns_unverified_not_green(monkeypatch):
    monkeypatch.setattr(views.web_security, "csrf_valid", lambda _request: True)
    client = app().test_client()
    # Test undecorated handler; real route still uses login_required.
    with app().test_request_context("/mission/raffles/command", method="POST",
                                    json={"action": "REVIEW", "territory": "uk",
                                          "kind": "free_draw", "sponsor_funded": True}):
        result = views.command.__wrapped__()
        body = result.get_json()
        assert result.status_code == 200
        assert body["ok"] is True and body["release_allowed"] is False
        assert body["actual_matrix_votes"] == []
        assert body["evidence_verified"] is False
    assert client.post("/mission/raffles/command",
                       json={"action": "OPEN_ENTRIES"}).status_code in (401, 403, 503)


def test_all_mutating_buttons_block_even_with_valid_csrf(monkeypatch):
    monkeypatch.setattr(views.web_security, "csrf_valid", lambda _request: True)
    for action in ("STOP", "RECOVER", "CONTINUE", "APPROVE_FOR_REVIEW",
                   "OPEN_ENTRIES", "TAKE_PAYMENT", "PUBLISH", "SELECT_WINNER"):
        with app().test_request_context("/mission/raffles/command", method="POST",
                                        json={"action": action}):
            response = views.command.__wrapped__()
            assert response.status_code == 423
            assert response.get_json()["execution_granted"] is False


def test_csrf_blocks_before_review(monkeypatch):
    monkeypatch.setattr(views.web_security, "csrf_valid", lambda _request: False)
    with app().test_request_context("/mission/raffles/command", method="POST",
                                    json={"action": "REVIEW"}):
        response = views.command.__wrapped__()
        assert response.status_code == 403
        assert response.get_json()["outcome"] == "BLOCKED_CSRF"


def test_template_button_handlers_and_private_registration():
    page = (ROOT / "mission_control/templates/raffles_command.html").read_text()
    initializer = (ROOT / "mission_control/__init__.py").read_text()
    assert 'data-action="STOP"' in page
    assert 'data-action="REVIEW"' in page
    assert 'data-action="APPROVE_FOR_REVIEW"' in page
    assert 'credentials:"same-origin"' in page
    assert "button.disabled=true" in page
    assert "register_blueprint(raffles_command_bp)" in initializer
