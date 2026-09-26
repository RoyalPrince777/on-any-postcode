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


def test_payment_controls_ignore_forged_owner_and_use_authenticated_owner(monkeypatch):
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

    monkeypatch.setattr(
        sika_global_views.sika_security_ledger,
        "latest_state",
        lambda owner_id: {
            "daily_limit_sika": "1000.00",
            "suspicious_device": False,
            "beneficiaries": [],
            "alerts": [],
            "durable": True,
            "money_moved": False,
            "founder_auth_touched": False,
        },
    )
    monkeypatch.setattr(
        sika_global_views.sika_security_ledger,
        "daily_payment_activity",
        lambda owner_id: {
            "daily_attempted_sika": "0.00",
            "daily_review_events": 0,
            "daily_hold_events": 0,
            "daily_executed_spend_sika": "0.00",
            "money_execution_enabled": False,
            "truth_mode": "attempted_not_executed_spend",
        },
    )
    monkeypatch.setattr(
        sika_global_views.sika_security_ledger,
        "beneficiary_age_minutes",
        lambda owner_id, beneficiary_id: 60,
    )

    def fake_intent(owner_id, *, beneficiary_id, amount_sika, reference=""):
        captured["owner_id"] = owner_id
        return {
            "payment_intent_id": "intent-1",
            "beneficiary_id": beneficiary_id,
            "amount_sika": str(amount_sika),
            "status": "security_review_only",
            "security_receipt_id": "receipt-1",
            "money_moved": False,
            "payment_execution_authorised": False,
        }

    monkeypatch.setattr(
        sika_global_views.sika_security_ledger,
        "create_payment_intent",
        fake_intent,
    )
    monkeypatch.setattr(
        sika_global_views.sika_security_ledger,
        "record_authenticated_owner",
        lambda *args, **kwargs: {"event_id": "receipt-2"},
    )
    monkeypatch.setattr(
        sika_global_views.sika_security_ledger,
        "create_step_up_for_payment_intent",
        lambda owner_id, **kwargs: {
            "challenge_id": "challenge-1",
            "status": "pending",
            "payment_intent_id": "intent-1",
            "payment_execution_authorised": False,
            "money_moved": False,
        },
    )

    response = app.test_client().post(
        "/api/sika/security/payment-controls",
        json={
            "owner_id": ATTACKER_OWNER,
            "beneficiary_id": "beneficiary-1",
            "amount_sika": "600",
            "reference": "test",
        },
    )
    body = response.get_json()
    assert response.status_code == 200
    assert captured["owner_id"] == AUTH_OWNER
    assert captured["owner_id"] != ATTACKER_OWNER
    assert body["payment_execution_authorised"] is False


def test_missing_csrf_blocks_payment_controls_before_security_ledger(monkeypatch):
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
    called = {"ledger": False}

    def should_not_run(*args, **kwargs):
        called["ledger"] = True
        raise AssertionError("security ledger must not run without CSRF")

    monkeypatch.setattr(
        sika_global_views.sika_security_ledger,
        "latest_state",
        should_not_run,
    )

    response = app.test_client().post(
        "/api/sika/security/payment-controls",
        json={"beneficiary_id": "beneficiary-1", "amount_sika": "50"},
    )
    assert response.status_code == 403
    assert response.get_json()["error"] == "csrf_failed"
    assert called["ledger"] is False


def test_unauthenticated_payment_controls_fail_closed(monkeypatch):
    app = _app()
    monkeypatch.setattr(
        sika_global_views.web_security,
        "current_authenticated_user",
        lambda: None,
    )
    response = app.test_client().post(
        "/api/sika/security/payment-controls",
        json={"beneficiary_id": "beneficiary-1", "amount_sika": "50"},
    )
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "authentication_required"


def test_payment_review_confirm_requires_gate_and_never_executes(monkeypatch):
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
        sika_global_views.sika_security_ledger,
        "final_payment_review_gate",
        lambda owner_id, **kwargs: {
            "challenge_id": "challenge-1",
            "payment_intent_id": "intent-1",
            "linked": True,
            "proof_bound": False,
            "approved_for_review": True,
            "allowed_to_final_review": False,
            "payment_execution_authorised": False,
            "money_moved": False,
        },
    )
    response = app.test_client().post(
        "/api/sika/security/payment-review/confirm",
        json={"challenge_id": "challenge-1", "payment_intent_id": "intent-1"},
    )
    body = response.get_json()
    assert response.status_code == 423
    assert body["confirmed_for_review"] is False
    assert body["payment_execution_authorised"] is False


def test_missing_csrf_blocks_step_up_proof_before_ledger(monkeypatch):
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
    called = {"ledger": False}

    def should_not_run(*args, **kwargs):
        called["ledger"] = True
        raise AssertionError("proof binding must not run without CSRF")

    monkeypatch.setattr(
        sika_global_views.sika_security_ledger,
        "bind_step_up_proof",
        should_not_run,
    )

    response = app.test_client().post(
        "/api/sika/security/step-up/proof",
        json={
            "challenge_id": "challenge-1",
            "payment_intent_id": "intent-1",
            "proof_method": "bank_app_password",
        },
    )
    assert response.status_code == 403
    assert response.get_json()["error"] == "csrf_failed"
    assert called["ledger"] is False


def test_unauthenticated_reauth_backoff_fails_closed(monkeypatch):
    app = _app()
    monkeypatch.setattr(
        sika_global_views.web_security,
        "current_authenticated_user",
        lambda: None,
    )
    response = app.test_client().get("/api/sika/security/reauth-backoff")
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "authentication_required"


def test_sika_session_activate_uses_authenticated_owner_and_bound_device(monkeypatch):
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

    def fake_activate(owner_id, *, device_id):
        captured["owner_id"] = owner_id
        captured["device_id"] = device_id
        return {
            "session_id": "session-1",
            "device_id": device_id,
            "status": "active",
            "founder_auth_touched": False,
            "money_execution_enabled": False,
        }

    monkeypatch.setattr(
        sika_global_views.sika_session_registry,
        "activate",
        fake_activate,
    )
    response = app.test_client().post(
        "/api/sika/security/session/activate",
        json={"owner_id": ATTACKER_OWNER, "device_id": "trusted-device"},
    )
    assert response.status_code == 201
    assert captured["owner_id"] == AUTH_OWNER
    assert captured["owner_id"] != ATTACKER_OWNER
    assert captured["device_id"] == "trusted-device"


def test_sika_session_activate_missing_csrf_blocks_registry(monkeypatch):
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
    called = {"registry": False}

    def should_not_run(*args, **kwargs):
        called["registry"] = True
        raise AssertionError("session registry must not run without CSRF")

    monkeypatch.setattr(
        sika_global_views.sika_session_registry,
        "activate",
        should_not_run,
    )
    response = app.test_client().post(
        "/api/sika/security/session/activate",
        json={"device_id": "trusted-device"},
    )
    assert response.status_code == 403
    assert response.get_json()["error"] == "csrf_failed"
    assert called["registry"] is False


def test_sika_session_registry_rejects_untrusted_device(monkeypatch):
    from mission_control import sika_session_registry

    monkeypatch.setattr(
        sika_session_registry.sika_device_binding_store,
        "read",
        lambda owner_id: {
            "owner_id": str(owner_id),
            "bound": True,
            "device_id": "trusted-device",
        },
    )
    try:
        sika_session_registry.activate(
            AUTH_OWNER,
            device_id="attacker-device",
        )
    except ValueError as exc:
        assert str(exc) == "trusted_bound_device_required"
    else:
        raise AssertionError("untrusted device must fail closed")


def test_sika_session_registry_compromise_lock_blocks_active_session(monkeypatch):
    from mission_control import sika_session_registry

    monkeypatch.setattr(
        sika_session_registry,
        "project",
        lambda owner_id: {
            "sessions": [{
                "session_id": "session-1",
                "device_id": "trusted-device",
                "status": "active",
            }],
            "active_sessions": [],
            "active_session_count": 0,
            "compromise_locked": True,
        },
    )
    try:
        sika_session_registry.require_active(AUTH_OWNER, "session-1")
    except PermissionError as exc:
        assert str(exc) == "sika_compromise_lock_active"
    else:
        raise AssertionError("compromise lock must fail closed")


def test_sika_revoke_all_is_owner_scoped(monkeypatch):
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

    def fake_revoke_all(owner_id, *, reason):
        captured["owner_id"] = owner_id
        return {
            "revoked_all": True,
            "active_session_count_before": 2,
            "founder_auth_touched": False,
        }

    monkeypatch.setattr(
        sika_global_views.sika_session_registry,
        "revoke_all",
        fake_revoke_all,
    )
    response = app.test_client().post(
        "/api/sika/security/session/revoke-all",
        json={"owner_id": ATTACKER_OWNER, "reason": "compromise"},
    )
    assert response.status_code == 200
    assert captured["owner_id"] == AUTH_OWNER
    assert captured["owner_id"] != ATTACKER_OWNER



def test_session_activate_uses_authenticated_owner_not_request_owner(monkeypatch):
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

    def fake_activate(owner_id, *, device_id):
        captured["owner_id"] = owner_id
        captured["device_id"] = device_id
        return {
            "session_id": "session-a",
            "device_id": device_id,
            "status": "active",
            "founder_auth_touched": False,
            "money_execution_enabled": False,
        }

    monkeypatch.setattr(
        sika_global_views.sika_session_registry,
        "activate",
        fake_activate,
    )

    response = app.test_client().post(
        "/api/sika/security/session/activate",
        json={"owner_id": ATTACKER_OWNER, "device_id": "device-a"},
    )
    body = response.get_json()
    assert response.status_code == 201
    assert captured["owner_id"] == AUTH_OWNER
    assert captured["owner_id"] != ATTACKER_OWNER
    assert body["money_execution_enabled"] is False


def test_missing_csrf_blocks_canonical_revoke_all_before_registry(monkeypatch):
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
    called = {"registry": False}

    def should_not_run(*args, **kwargs):
        called["registry"] = True
        raise AssertionError("session registry must not run without CSRF")

    monkeypatch.setattr(
        sika_global_views.sika_session_registry,
        "revoke_all",
        should_not_run,
    )

    response = app.test_client().post(
        "/api/sika/security/session/revoke-all",
        json={"reason": "test"},
    )
    assert response.status_code == 403
    assert response.get_json()["error"] == "csrf_failed"
    assert called["registry"] is False


def test_unauthenticated_session_registry_fails_closed(monkeypatch):
    app = _app()
    monkeypatch.setattr(
        sika_global_views.web_security,
        "current_authenticated_user",
        lambda: None,
    )
    response = app.test_client().get("/api/sika/security/sessions")
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "authentication_required"


def test_compromise_lock_uses_authenticated_owner_and_never_moves_money(monkeypatch):
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

    def fake_lock(owner_id, *, reason):
        captured["owner_id"] = owner_id
        captured["reason"] = reason
        return {
            "compromise_locked": True,
            "all_sessions_revoked": True,
            "money_execution_enabled": False,
            "founder_auth_touched": False,
        }

    monkeypatch.setattr(
        sika_global_views.sika_session_registry,
        "compromise_lock",
        fake_lock,
    )

    response = app.test_client().post(
        "/api/sika/security/compromise-lock",
        json={"owner_id": ATTACKER_OWNER, "reason": "suspected compromise"},
    )
    body = response.get_json()
    assert response.status_code == 200
    assert captured["owner_id"] == AUTH_OWNER
    assert body["compromise_locked"] is True
    assert body["money_execution_enabled"] is False
    assert body["founder_auth_touched"] is False


def test_compromise_recovery_uses_authenticated_owner(monkeypatch):
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

    def fake_recover(owner_id, *, trusted_device_id):
        captured["owner_id"] = owner_id
        captured["device_id"] = trusted_device_id
        return {
            "compromise_locked": False,
            "recovered": True,
            "trusted_device_id": trusted_device_id,
            "new_session_required": True,
            "founder_auth_touched": False,
        }

    monkeypatch.setattr(
        sika_global_views.sika_session_registry,
        "recover",
        fake_recover,
    )

    response = app.test_client().post(
        "/api/sika/security/compromise-recover",
        json={"owner_id": ATTACKER_OWNER, "device_id": "device-a"},
    )
    body = response.get_json()
    assert response.status_code == 200
    assert captured["owner_id"] == AUTH_OWNER
    assert captured["owner_id"] != ATTACKER_OWNER
    assert body["recovered"] is True
    assert body["new_session_required"] is True
