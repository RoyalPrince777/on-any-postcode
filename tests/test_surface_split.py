from pathlib import Path

import pytest
from flask import Flask

import smi_gateway
from mission_control import surface_security


def test_public_origin_hands_off_safe_aliases_and_hides_other_private_paths(monkeypatch):
    monkeypatch.setenv("OAP_SURFACE_ROLE", "public")
    monkeypatch.setenv("OAP_SMI_GATEWAY_SECRET", "s" * 48)
    monkeypatch.setenv("OAP_PRIVATE_SMI_ORIGIN", "https://oap-smi.onrender.com")
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

    @app.get("/the-spot/my-world")
    def spot_my_world():
        return "private"

    @app.get("/infrastructure")
    def infrastructure():
        return "private"

    @app.get("/world")
    def world():
        return "public"

    client = app.test_client()

    handoff = client.get("/mission")
    assert handoff.status_code == 302
    assert handoff.headers["Location"] == "https://oap-smi.onrender.com/mission/ollama"
    assert handoff.headers["Cache-Control"] == "no-store"
    assert handoff.headers["X-OAP-Private-Handoff"] == "smi-gateway"

    my_world_handoff = client.get("/my-world")
    assert my_world_handoff.status_code == 302
    assert my_world_handoff.headers["Location"] == "https://oap-smi.onrender.com/my-world"

    for path in (
        "/auth",
        "/enter-my-world",
        "/the-spot/my-world",
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


def test_public_surface_still_fails_closed_if_gateway_secret_is_missing(monkeypatch):
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

    @app.get("/the-spot/my-world")
    def spot_my_world():
        return "private"

    client = app.test_client()
    assert client.get("/mission").status_code == 302
    assert client.get("/auth").status_code == 404
    assert client.get("/the-spot/my-world").status_code == 404
    forged = client.get("/mission", headers={"X-OAP-SMI-Gateway": "x" * 48})
    assert forged.status_code == 302
    assert forged.headers["Location"].endswith("/mission/ollama")


def test_trusted_gateway_repairs_stale_private_aliases(monkeypatch):
    monkeypatch.setenv("OAP_SURFACE_ROLE", "public")
    monkeypatch.setenv("OAP_SMI_GATEWAY_SECRET", "s" * 48)
    app = Flask(__name__)
    surface_security.register(app)
    client = app.test_client()
    headers = {"X-OAP-SMI-Gateway": "s" * 48}

    smi = client.get("/mission/smi", headers=headers)
    assert smi.status_code == 302
    assert smi.headers["Location"].endswith("/mission/ollama")

    isac = client.get("/mission/isac", headers=headers)
    assert isac.status_code == 302
    assert isac.headers["Location"].endswith("/mission/isac-spatial/")


def test_public_aliases_handoff_to_correct_private_gateway_paths(monkeypatch):
    monkeypatch.setenv("OAP_SURFACE_ROLE", "public")
    monkeypatch.setenv("OAP_SMI_GATEWAY_SECRET", "s" * 48)
    monkeypatch.setenv("OAP_PRIVATE_SMI_ORIGIN", "https://private.example.test")
    app = Flask(__name__)
    surface_security.register(app)
    client = app.test_client()

    expected = {
        "/smi": "/mission/ollama",
        "/mission": "/mission/ollama",
        "/mission/smi": "/mission/ollama",
        "/mission/ollama": "/mission/ollama",
        "/war-room": "/mission/war-room",
        "/mission/war-room": "/mission/war-room",
        "/mission/isac": "/mission/isac-spatial/",
        "/my-world": "/my-world",
        "/myworld": "/my-world",
    }
    for source, target in expected.items():
        response = client.get(source)
        assert response.status_code == 302
        assert response.headers["Location"] == f"https://private.example.test{target}"


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


def test_smi_gateway_requires_an_exact_https_public_origin(monkeypatch):
    monkeypatch.setenv("OAP_PUBLIC_ORIGIN", "https://public.example.test/")
    assert smi_gateway._origin() == "https://public.example.test"

    for invalid in (
        "http://public.example.test",
        "https://public.example.test/private",
        "https://public.example.test?secret=value",
        "https://user:password@public.example.test",
        "https://public.example.test:not-a-port",
    ):
        monkeypatch.setenv("OAP_PUBLIC_ORIGIN", invalid)
        with pytest.raises(RuntimeError, match="invalid_public_origin"):
            smi_gateway._origin()


def test_smi_gateway_healthz_is_process_local(monkeypatch):
    monkeypatch.delenv("OAP_SMI_GATEWAY_SECRET", raising=False)
    monkeypatch.setenv("RENDER_GIT_COMMIT", "0123456789abcdef0123456789abcdef01234567")

    def must_not_proxy(_path):
        raise AssertionError("healthz_must_not_proxy")

    monkeypatch.setattr(smi_gateway, "_proxy", must_not_proxy)
    client = smi_gateway.app.test_client()

    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.get_json() == {
        "status": "ok",
        "service": "oap-smi-gateway",
        "scope": "process",
        "revision": "0123456789ab",
    }
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-OAP-Health-Scope"] == "process"
    assert response.headers["X-OAP-Surface"] == "sovereign-megaverse-intelligence"
    assert client.head("/healthz").status_code == 200


def test_smi_gateway_healthz_revision_fails_safe(monkeypatch):
    monkeypatch.delenv("RENDER_GIT_COMMIT", raising=False)
    monkeypatch.setenv("OAP_ENV_REVISION", " release/alpha secret? ")
    assert smi_gateway._revision() == "releasealpha"

    monkeypatch.delenv("OAP_ENV_REVISION", raising=False)
    assert smi_gateway._revision() == "unknown"


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


def test_smi_gateway_root_returns_founder_to_personal_smi():
    client = smi_gateway.app.test_client()
    response = client.get("/")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/auth?next=/mission/ollama")


def test_render_blueprint_keeps_smi_free_and_contains_no_paid_worker():
    content = Path("render.yaml").read_text()
    assert "name: oap-smi" in content
    assert "startCommand: gunicorn smi_gateway:app" in content
    assert "type: worker" not in content

    smi_block = content.split("name: oap-smi", 1)[1].split("  - type:", 1)[0]
    assert "plan: free" in smi_block
    assert "plan: starter" not in smi_block

    routing_block = content.split("name: oap-routing", 1)[1]
    assert "runtime: docker" in routing_block
    assert "plan: starter" in routing_block
