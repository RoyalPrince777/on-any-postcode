from __future__ import annotations

from flask import Flask

from mission_control import sika_global_views

AUTH_OWNER = "11111111-1111-4111-8111-111111111111"
ATTACKER_OWNER = "22222222-2222-4222-8222-222222222222"


def _app():
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


def test_android_evidence_routes_are_registered():
    app = _app()
    rules = {rule.rule: set(rule.methods) for rule in app.url_map.iter_rules()}
    assert "POST" in rules["/api/sika/android/evidence"]
    assert "GET" in rules["/api/sika/android/evidence/latest"]
    assert "GET" in rules["/api/sika/android/evidence/readiness"]


def test_android_evidence_uses_authenticated_owner_not_request_owner(monkeypatch):
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

    def fake_record(owner_id, body):
        captured["owner_id"] = owner_id
        captured["body"] = body
        return {
            "real_android_pwa_acceptance": False,
            "public_install_release_gate": False,
            "founder_auth_touched": False,
        }

    monkeypatch.setattr(
        sika_global_views.sika_android_evidence_store,
        "record_authenticated_owner",
        fake_record,
    )

    response = app.test_client().post(
        "/api/sika/android/evidence",
        json={
            "owner_id": ATTACKER_OWNER,
            "device_label": "real-android-device",
            "install_completed": True,
        },
    )
    body = response.get_json()
    assert response.status_code == 201
    assert captured["owner_id"] == AUTH_OWNER
    assert captured["owner_id"] != ATTACKER_OWNER
    assert body["caller_supplied_owner_id_trusted"] is False


def test_missing_csrf_blocks_android_evidence_write(monkeypatch):
    app = _app()
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
        raise AssertionError("store must not run")

    monkeypatch.setattr(
        sika_global_views.sika_android_evidence_store,
        "record_authenticated_owner",
        should_not_run,
    )

    response = app.test_client().post(
        "/api/sika/android/evidence",
        json={"install_completed": True},
    )
    assert response.status_code == 403
    assert called["store"] is False


def test_android_acceptance_stays_closed_without_complete_real_evidence(monkeypatch):
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
    monkeypatch.setattr(
        sika_global_views.sika_android_evidence_store,
        "record_authenticated_owner",
        lambda owner_id, body: {
            "real_android_pwa_acceptance": False,
            "public_install_release_gate": False,
            "reason": "physical_android_evidence_required",
            "founder_auth_touched": False,
        },
    )
    response = app.test_client().post(
        "/api/sika/android/evidence",
        json={
            "device_label": "real-android-device",
            "install_completed": True,
            "user_confirmed": True,
        },
    )
    body = response.get_json()
    assert response.status_code == 201
    assert body["real_android_pwa_acceptance"] is False
    assert body["public_install_release_gate"] is False
