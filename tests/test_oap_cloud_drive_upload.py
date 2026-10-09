import base64
import hashlib

from flask import Flask

from oap_cloud import founder_control
from oap_cloud.founder_control import cloud_bp


def test_drive_upload_requires_founder_token(monkeypatch, tmp_path):
    monkeypatch.setenv("OAP_CLOUD_FOUNDER_TOKEN", "test-founder-secret")
    monkeypatch.setenv("OAP_DRIVE_STORAGE_ROOT", str(tmp_path))
    app = Flask(__name__)
    app.secret_key = "test-only-cloud-session-secret"
    app.register_blueprint(cloud_bp)
    client = app.test_client()
    # Token alone must fail, even when storage exists.
    assert client.get("/cloud/v1/status", headers={"Authorization": "Bearer test-founder-secret"}).status_code == 404
    monkeypatch.setattr(founder_control.web_security, "current_authenticated_user", lambda: {"id": "founder"})
    monkeypatch.setattr(founder_control.web_security, "private_authority_allowed", lambda user: True)
    with client.session_transaction() as sess:
        sess["oap_csrf_token"] = "test-csrf-token-0123456789abcdef"
    payload = b"test-build-log"
    manifest = {
        "kind": "build-log",
        "size_bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "payload_base64": base64.b64encode(payload).decode("ascii"),
    }
    route = "/cloud/v1/drive/artifacts"
    assert client.post(route, json=manifest).status_code == 404
    assert client.post(route, json=manifest, headers={"Authorization": "Bearer wrong"}).status_code == 404
    assert client.post(route, json=manifest, headers={"Authorization": "Bearer test-founder-secret"}).status_code == 404
    assert client.post(route, json=manifest, headers={"Authorization": "Bearer test-founder-secret", "X-OAP-CSRF": "wrong-token"}).status_code == 404
    response = client.post(
        route, json=manifest, headers={"Authorization": "Bearer test-founder-secret", "X-OAP-CSRF": "test-csrf-token-0123456789abcdef"}
    )
    assert response.status_code == 201
    assert response.json["sha256"] == manifest["sha256"]
    assert (tmp_path / manifest["sha256"]).read_bytes() == payload
    retrieve = "/cloud/v1/drive/retrieve"
    clean = {k: v for k, v in manifest.items() if k != "payload_base64"}
    assert client.post(retrieve, json=clean).status_code == 404
    assert client.post(retrieve, json=clean, headers={"Authorization": "Bearer test-founder-secret"}).status_code == 404
    fetched = client.post(retrieve, json=clean, headers={"Authorization": "Bearer test-founder-secret", "X-OAP-CSRF": "test-csrf-token-0123456789abcdef"})
    assert fetched.status_code == 200
    assert base64.b64decode(fetched.json["payload_base64"]) == payload
    (tmp_path / manifest["sha256"]).write_bytes(b"corrupted")
    rejected = client.post(retrieve, json=clean, headers={"Authorization": "Bearer test-founder-secret", "X-OAP-CSRF": "test-csrf-token-0123456789abcdef"})
    assert rejected.status_code == 404


def test_drive_upload_fails_closed_without_storage(monkeypatch):
    monkeypatch.setenv("OAP_CLOUD_FOUNDER_TOKEN", "test-founder-secret")
    monkeypatch.delenv("OAP_DRIVE_STORAGE_ROOT", raising=False)
    app = Flask(__name__)
    app.secret_key = "test-only-cloud-session-secret"
    app.register_blueprint(cloud_bp)
    monkeypatch.setattr(founder_control.web_security, "current_authenticated_user", lambda: {"id": "founder"})
    monkeypatch.setattr(founder_control.web_security, "private_authority_allowed", lambda user: True)
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["oap_csrf_token"] = "test-csrf-token-0123456789abcdef"
    response = client.post(
        "/cloud/v1/drive/artifacts",
        json={},
        headers={"Authorization": "Bearer test-founder-secret", "X-OAP-CSRF": "test-csrf-token-0123456789abcdef"},
    )
    assert response.status_code == 503


def test_cloud_denies_non_founder_and_recovery_identity(monkeypatch):
    monkeypatch.setenv("OAP_CLOUD_FOUNDER_TOKEN", "test-founder-secret")
    app = Flask(__name__)
    app.secret_key = "test-only-cloud-session-secret"
    app.register_blueprint(cloud_bp)
    client = app.test_client()
    headers = {"Authorization": "Bearer test-founder-secret"}
    monkeypatch.setattr(founder_control.web_security, "current_authenticated_user", lambda: {"id": "member"})
    monkeypatch.setattr(founder_control.web_security, "private_authority_allowed", lambda user: False)
    assert client.get("/cloud/v1/status", headers=headers).status_code == 404
    monkeypatch.setattr(founder_control.web_security, "current_authenticated_user", lambda: {"id": "founder", "recovery_founder": True})
    monkeypatch.setattr(founder_control.web_security, "private_authority_allowed", lambda user: True)
    assert client.get("/cloud/v1/status", headers=headers).status_code == 404


def test_cloud_rejects_oversized_and_unknown_length_requests(monkeypatch, tmp_path):
    monkeypatch.setenv("OAP_CLOUD_FOUNDER_TOKEN", "test-founder-secret")
    monkeypatch.setenv("OAP_DRIVE_STORAGE_ROOT", str(tmp_path))
    app = Flask(__name__)
    app.secret_key = "test-only-cloud-session-secret"
    app.register_blueprint(cloud_bp)
    monkeypatch.setattr(founder_control.web_security, "current_authenticated_user", lambda: {"id": "founder"})
    monkeypatch.setattr(founder_control.web_security, "private_authority_allowed", lambda user: True)
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["oap_csrf_token"] = "test-csrf-token-0123456789abcdef"
    headers = {"Authorization": "Bearer test-founder-secret", "X-OAP-CSRF": "test-csrf-token-0123456789abcdef"}
    assert client.post("/cloud/v1/drive/artifacts", data=b"x" * 20_000_001, headers=headers).status_code == 413
    assert client.post("/cloud/v1/drive/retrieve", data=b"x" * 4097, headers=headers).status_code == 413
    assert client.post("/cloud/v1/drive/artifacts", data=b"", headers=headers).status_code == 400
