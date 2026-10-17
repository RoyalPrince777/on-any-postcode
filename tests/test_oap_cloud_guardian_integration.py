"""Founder/Guardian integration contract using real OAP authorization functions.

The Cloud blueprint is registered ONLY on an isolated Flask test app.
No storage or cloud infrastructure is provisioned.
"""
from flask import Flask

from mission_control import web_security
from oap_cloud.founder_control import cloud_bp


def _client(monkeypatch, *, token="cloud-test-secret"):
    monkeypatch.setenv("OAP_CLOUD_FOUNDER_TOKEN", token)
    monkeypatch.delenv("OAP_DRIVE_STORAGE_ROOT", raising=False)
    app = Flask(__name__)
    app.secret_key = "test-only-managed-session"
    app.register_blueprint(cloud_bp)
    return app.test_client()


def test_no_managed_identity_even_with_valid_bootstrap_token(monkeypatch):
    client = _client(monkeypatch)
    monkeypatch.setattr(web_security, "current_authenticated_user", lambda: None)
    response = client.get("/cloud/v1/status", headers={"Authorization": "Bearer cloud-test-secret"})
    assert response.status_code == 404


def test_actual_authority_policy_denies_unconfigured_member(monkeypatch):
    client = _client(monkeypatch)
    member = {"id": "00000000-0000-4000-8000-000000000001",
              "email": "ordinary-member@example.invalid", "email_verified": False}
    monkeypatch.setattr(web_security, "current_authenticated_user", lambda: member)
    monkeypatch.setattr(web_security.authority, "identity_is_authority", lambda identity: False)
    monkeypatch.setattr(web_security.authority, "email_is_authority", lambda email: False)
    monkeypatch.setattr(web_security.postgres_db, "connect", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("db unavailable")))
    response = client.get("/cloud/v1/status", headers={"Authorization": "Bearer cloud-test-secret"})
    assert response.status_code == 404


def test_recovery_identity_denied_before_authority_lookup(monkeypatch):
    client = _client(monkeypatch)
    monkeypatch.setattr(web_security, "current_authenticated_user",
                        lambda: {"id": "recovery", "recovery_founder": True})
    response = client.get("/cloud/v1/status", headers={"Authorization": "Bearer cloud-test-secret"})
    assert response.status_code == 404


def test_managed_founder_policy_and_csrf_storage_boundary(monkeypatch):
    client = _client(monkeypatch)
    founder = {"id": "00000000-0000-4000-8000-000000000002",
               "email": "founder@example.invalid", "email_verified": False}
    monkeypatch.setattr(web_security, "current_authenticated_user", lambda: founder)
    monkeypatch.setattr(web_security.authority, "identity_is_authority",
                        lambda identity: identity == founder["id"])
    headers = {"Authorization": "Bearer cloud-test-secret"}
    assert client.get("/cloud/v1/status").status_code == 404
    response = client.get("/cloud/v1/status", headers=headers)
    assert response.status_code == 200
    assert response.json["storage"] == "not_provisioned"
    assert client.post("/cloud/v1/drive/artifacts", json={}, headers=headers).status_code == 404
    with client.session_transaction() as session:
        session[web_security.CSRF_SESSION_KEY] = "test-csrf-secret"
    headers["X-OAP-CSRF"] = "test-csrf-secret"
    response = client.post("/cloud/v1/drive/artifacts", json={}, headers=headers)
    assert response.status_code == 503
    assert response.json["error"] == "storage_not_provisioned"
