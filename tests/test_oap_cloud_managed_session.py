"""Exercise the canonical OAP session parser through Cloud's isolated blueprint.

Only the provider response is substituted; Cloud identity and authority functions
are real. This is a software integration contract, not live Neon authentication.
"""
from flask import Flask

from mission_control import neon_auth, web_security
from oap_cloud.founder_control import cloud_bp

FOUNDER_ID = "00000000-0000-4000-8000-000000000042"
MEMBER_ID = "00000000-0000-4000-8000-000000000043"


def test_cloud_uses_canonical_managed_session_pipeline(monkeypatch):
    monkeypatch.setenv("OAP_CLOUD_FOUNDER_TOKEN", "cloud-test-bootstrap")
    monkeypatch.delenv("OAP_DRIVE_STORAGE_ROOT", raising=False)
    app = Flask(__name__)
    app.secret_key = "isolated-test-only"
    app.register_blueprint(cloud_bp)
    client = app.test_client()

    # Mock the external identity provider boundary, not OAP's session parser.
    def provider_session(cookie_header):
        return neon_auth.AuthResult(
            status_code=200,
            payload={"session": {"id": "provider-session"},
                     "user": {"id": FOUNDER_ID, "email": "founder@example.invalid",
                              "emailVerified": False, "banned": False}},
        )

    monkeypatch.setattr(web_security.founder_recovery, "recovery_user", lambda: None)
    monkeypatch.setattr(web_security, "auth_cookie_header", lambda: "oap-auth=test-session")
    monkeypatch.setattr(neon_auth, "get_session", provider_session)
    monkeypatch.setattr(web_security.authority, "identity_is_authority",
                        lambda identity: identity == FOUNDER_ID)

    headers = {"Authorization": "Bearer cloud-test-bootstrap"}
    assert client.get("/cloud/v1/status").status_code == 404
    response = client.get("/cloud/v1/status", headers=headers)
    assert response.status_code == 200
    assert response.json["storage"] == "not_provisioned"

    # Provider rejects the session: even the correct bootstrap token fails.
    monkeypatch.setattr(neon_auth, "get_session",
                        lambda cookie: neon_auth.AuthResult(status_code=401, payload={}))
    assert client.get("/cloud/v1/status", headers=headers).status_code == 404

    # A banned user cannot gain access even with a valid provider session.
    monkeypatch.setattr(neon_auth, "get_session",
                        lambda cookie: neon_auth.AuthResult(
                            status_code=200,
                            payload={"session": {"id": "provider-session"},
                                     "user": {"id": FOUNDER_ID, "banned": True}}))
    assert client.get("/cloud/v1/status", headers=headers).status_code == 404

    # Invalid provider identity is denied by canonical UUID validation.
    monkeypatch.setattr(neon_auth, "get_session",
                        lambda cookie: neon_auth.AuthResult(
                            status_code=200,
                            payload={"session": {"id": "provider-session"},
                                     "user": {"id": "not-a-uuid"}}))
    assert client.get("/cloud/v1/status", headers=headers).status_code == 404
