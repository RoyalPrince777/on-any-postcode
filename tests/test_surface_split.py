from pathlib import Path

from flask import Flask

import smi_gateway
from mission_control import surface_security


def test_public_origin_hides_all_founder_surfaces_behind_gateway(monkeypatch):
    monkeypatch.setenv("OAP_SURFACE_ROLE", "public")
    monkeypatch.setenv("OAP_SMI_GATEWAY_SECRET", "s" * 48)
    app = Flask(__name__)
    surface_security.register(app)

    @app.get("/mission")
    def mission():
        return "private"

    @app.get("/auth")
    def auth():
        return "sign-in"

    @app.get("/enter-my-world")
    def enter_my_world():
        return "sign-in"

    @app.get("/my-world")
    def my_world():
        return "private"

    @app.get("/infrastructure")
    def infrastructure():
        return "private"

    @app.get("/world")
    def world():
        return "public"

    client = app.test_client()
    for path in (
        "/mission",
        "/auth",
        "/enter-my-world",
        "/my-world",
        "/infrastructure",
        "/api/infrastructure/status",
    ):
        blocked = client.get(path)
        assert blocked.status_code == 404
        assert blocked.headers["Cache-Control"] == "no-store"
    assert client.get("/world").status_code == 200

    for path in ("/mission", "/auth", "/my-world", "/infrastructure"):
        allowed = client.get(path, headers={"X-OAP-SMI-Gateway": "s" * 48})
        assert allowed.status_code == 200


def test_public_surface_fails_closed_even_if_gateway_secret_is_missing(monkeypatch):
    monkeypatch.setenv("OAP_SURFACE_ROLE", "public")
    monkeypatch.delenv("OAP_SMI_GATEWAY_SECRET", raising=False)
    app = Flask(__name__)
    surface_security.register(app)

    @app.get("/mission")
    def mission():
        return "private"

    @app.get("/auth")
    def auth():
        return "sign-in"

    client = app.test_client()
    assert client.get("/mission").status_code == 404
    assert client.get("/auth").status_code == 404
    assert client.get("/mission", headers={"X-OAP-SMI-Gateway": "x" * 48}).status_code == 404


def test_smi_gateway_allowlist_is_founder_private_only():
    assert smi_gateway._allowed("mission") is True
    assert smi_gateway._allowed("mission/brain") is True
    assert smi_gateway._allowed("auth") is True
    assert smi_gateway._allowed("auth/sign-in") is True
    assert smi_gateway._allowed("auth/sign-out") is True
    assert smi_gateway._allowed("enter-my-world") is True
    assert smi_gateway._allowed("my-world") is True
    assert smi_gateway._allowed("my-world/settings") is True
    assert smi_gateway._allowed("infrastructure") is True
    assert smi_gateway._allowed("infrastructure/security") is True
    assert smi_gateway._allowed("api/infrastructure/status") is True
    assert smi_gateway._allowed("healthz") is True
    assert smi_gateway._allowed("assets/oap.css") is True
    assert smi_gateway._allowed("auth/sign-up") is False
    assert smi_gateway._allowed("activate-founder") is False
    assert smi_gateway._allowed("world") is False
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


def test_smi_gateway_root_redirects_to_private_sign_in():
    client = smi_gateway.app.test_client()
    response = client.get("/")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/auth")


def test_render_blueprint_is_free_and_contains_no_paid_worker():
    content = Path("render.yaml").read_text()
    assert "name: oap-smi" in content
    assert "type: web" in content
    assert "plan: free" in content
    assert "startCommand: gunicorn smi_gateway:app" in content
    assert "type: worker" not in content
    assert "plan: starter" not in content
