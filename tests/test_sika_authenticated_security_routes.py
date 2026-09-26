from __future__ import annotations

from flask import Flask

from mission_control import sika_global_views


AUTH_OWNER = "11111111-1111-4111-8111-111111111111"
ATTACKER_OWNER = "22222222-2222-4222-8222-222222222222"


def _app() -> Flask:
    app = Flask(__name__)
    app.secret_key = "test-secret"
    app.register_blueprint(sika_global_views.bp)
    return app


def _auth_user():
    return {
        "id": AUTH_OWNER,
        "name": "OAP Member",
        "email": "member@example.test",
        "email_verified": True,
    }


def test_authenticated_sika_security_routes_are_registered():
    app = _app()
    rules = {rule.rule: set(rule.methods) for rule in app.url_map.iter_rules()}
    assert "POST" in rules["/api/sika/security/credential/create"]
    assert "POST" in rules["/api/sika/security/credential/verify"]
    assert "POST" in rules["/api/sika/security/credential/recover"]
    assert "POST" in rules["/api/sika/device/bind"]
    assert "GET" in rules["/api/sika/device/status"]
    assert "POST" in rules["/api/sika/device/recover"]


def test_credential_create_uses_server_authenticated_owner_not_request_owner(monkeypatch):
    app = _app()
    sika_global_views._SIKA_SECURITY_LIMITER.reset()
    monkeypatch.setattr(
        sika_global_views.web_security,
        "current_authenticated_user",
        lambda: _auth_user(),
    )
    monkeypatch.setattr(
        sika_global_views.web_security,
        "csrf_valid",
        lambda request: True,
    )
    captured = {}

    def fake_create(owner_id, password):
        captured["owner_id"] = owner_id
        captured["password"] = password
        return {
            "created": True,
            "owner_id": owner_id,
            "password_hash_returned": False,
            "founder_auth_touched": False,
        }

    monkeypatch.setattr(
        sika_global_views.sika_bank_credential_store,
        "create_authenticated_owner",
        fake_create,
    )

    response = app.test_client().post(
        "/api/sika/security/credential/create",
        json={
            "owner_id": ATTACKER_OWNER,
            "password": "strong-bank-app-passphrase",
        },
    )
    body = response.get_json()
    assert response.status_code == 201
    assert captured["owner_id"] == AUTH_OWNER
    assert captured["owner_id"] != ATTACKER_OWNER
    assert body["caller_supplied_owner_id_trusted"] is False
    assert body["authenticated_owner_source"] == "oap_authenticated_session"


def test_missing_csrf_blocks_credential_mutation_before_store(monkeypatch):
    app = _app()
    sika_global_views._SIKA_SECURITY_LIMITER.reset()
    monkeypatch.setattr(
        sika_global_views.web_security,
        "current_authenticated_user",
        lambda: _auth_user(),
    )
    monkeypatch.setattr(
        sika_global_views.web_security,
        "csrf_valid",
        lambda request: False,
    )
    called = {"store": False}

    def should_not_run(*args, **kwargs):
        called["store"] = True
        raise AssertionError("credential store must not run without CSRF")

    monkeypatch.setattr(
        sika_global_views.sika_bank_credential_store,
        "create_authenticated_owner",
        should_not_run,
    )

    response = app.test_client().post(
        "/api/sika/security/credential/create",
        json={"password": "strong-bank-app-passphrase"},
    )
    assert response.status_code == 403
    assert response.get_json()["error"] == "csrf_failed"
    assert called["store"] is False


def test_device_bind_uses_server_authenticated_owner_not_request_owner(monkeypatch):
    app = _app()
    monkeypatch.setattr(
        sika_global_views.web_security,
        "current_authenticated_user",
        lambda: _auth_user(),
    )
    monkeypatch.setattr(
        sika_global_views.web_security,
        "csrf_valid",
        lambda request: True,
    )
    captured = {}

    def fake_bind(owner, device_id):
        captured["owner_id"] = owner.owner_id
        captured["source"] = owner.source
        captured["device_id"] = device_id
        return {
            "bound": True,
            "owner_id": owner.owner_id,
            "device_id": device_id,
            "authenticated_owner_source": owner.source,
            "caller_supplied_owner_id_trusted": False,
            "founder_auth_touched": False,
        }

    monkeypatch.setattr(
        sika_global_views.sika_authenticated_owner_adapter,
        "bind",
        fake_bind,
    )

    response = app.test_client().post(
        "/api/sika/device/bind",
        json={
            "owner_id": ATTACKER_OWNER,
            "device_id": "member-device-a",
        },
    )
    body = response.get_json()
    assert response.status_code == 201
    assert captured["owner_id"] == AUTH_OWNER
    assert captured["owner_id"] != ATTACKER_OWNER
    assert captured["source"] == "oap_authenticated_session"
    assert body["caller_supplied_owner_id_trusted"] is False


def test_unauthenticated_sika_security_route_fails_closed(monkeypatch):
    app = _app()
    monkeypatch.setattr(
        sika_global_views.web_security,
        "current_authenticated_user",
        lambda: None,
    )
    response = app.test_client().post(
        "/api/sika/security/credential/create",
        json={"password": "strong-bank-app-passphrase"},
    )
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "authentication_required"
