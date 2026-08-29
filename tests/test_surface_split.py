from pathlib import Path

from flask import Flask

import smi_gateway
from mission_control import surface_security


def test_public_origin_hides_mission_behind_gateway(monkeypatch):
    monkeypatch.setenv("OAP_SMI_GATEWAY_SECRET", "s" * 48)
    app = Flask(__name__)
    surface_security.register(app)

    @app.get("/mission")
    def mission():
        return "private"

    @app.get("/world")
    def world():
        return "public"

    client = app.test_client()
    blocked = client.get("/mission")
    assert blocked.status_code == 404
    assert blocked.headers["Cache-Control"] == "no-store"
    assert client.get("/world").status_code == 200

    allowed = client.get(
        "/mission", headers={"X-OAP-SMI-Gateway": "s" * 48}
    )
    assert allowed.status_code == 200


def test_gateway_staging_is_backward_compatible_until_secret_exists(monkeypatch):
    monkeypatch.delenv("OAP_SMI_GATEWAY_SECRET", raising=False)
    app = Flask(__name__)
    surface_security.register(app)

    @app.get("/mission")
    def mission():
        return "private"

    assert app.test_client().get("/mission").status_code == 200


def test_smi_gateway_allowlist_is_private_and_sign_in_only():
    assert smi_gateway._allowed("mission") is True
    assert smi_gateway._allowed("mission/brain") is True
    assert smi_gateway._allowed("auth") is True
    assert smi_gateway._allowed("auth/sign-in") is True
    assert smi_gateway._allowed("auth/sign-out") is True
    assert smi_gateway._allowed("enter-my-world") is True
    assert smi_gateway._allowed("healthz") is True
    assert smi_gateway._allowed("assets/oap.css") is True
    assert smi_gateway._allowed("auth/sign-up") is False
    assert smi_gateway._allowed("activate-founder") is False
    assert smi_gateway._allowed("world") is False
    assert smi_gateway._allowed("my-world") is False
    assert smi_gateway._allowed("market") is False
    assert smi_gateway._allowed("manifest.webmanifest") is False
    assert smi_gateway._allowed("service-worker.js") is False


def test_smi_gateway_does_not_follow_upstream_redirects():
    assert any(
        isinstance(handler, smi_gateway._NoRedirect)
        for handler in smi_gateway._OPENER.handlers
    )
    handler = smi_gateway._NoRedirect()
    assert handler.redirect_request(
        None,
        None,
        302,
        "Found",
        {},
        "https://example.test/auth",
    ) is None


def test_smi_gateway_root_redirects_to_private_workspace():
    client = smi_gateway.app.test_client()
    response = client.get("/")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/mission")


def test_render_blueprint_is_free_and_contains_no_paid_worker():
    content = Path("render.yaml").read_text()
    assert "name: oap-smi" in content
    assert "type: web" in content
    assert "plan: free" in content
    assert "startCommand: gunicorn smi_gateway:app" in content
    assert "type: worker" not in content
    assert "plan: starter" not in content
