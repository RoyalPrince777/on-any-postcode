from pathlib import Path

import pytest
from flask import Flask

import smi_gateway
from mission_control import surface_security


def test_public_origin_hands_off_safe_aliases_and_hides_other_private_paths(monkeypatch):
    monkeypatch.setenv("OAP_SURFACE_ROLE", "public")
    monkeypatch.setenv("OAP_SMI_GATEWAY_SECRET", "s" * 48)
    monkeypatch.setenv("OAP_PRIVATE_SMI_ORIGIN", "https://smi.onanypostcode.global")
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
    assert handoff.headers["Location"] == "https://smi.onanypostcode.global/mission/ollama"
    assert handoff.headers["Cache-Control"] == "no-store"
    assert handoff.headers["X-OAP-Private-Handoff"] == "smi-gateway"

    my_world_handoff = client.get("/my-world")
    assert my_world_handoff.status_code == 302
    assert my_world_handoff.headers["Location"] == "https://smi.onanypostcode.global/my-world"

    auth_handoff = client.get("/enter-my-world?next=/global-affairs")
    assert auth_handoff.status_code == 302
    assert auth_handoff.headers["Location"] == (
        "https://smi.onanypostcode.global/enter-my-world?next=/global-affairs"
    )

    auth_alias_handoff = client.get("/auth?next=/mission/ollama")
    assert auth_alias_handoff.status_code == 302
    assert auth_alias_handoff.headers["Location"] == (
        "https://smi.onanypostcode.global/auth?next=/mission/ollama"
    )

    for path in (
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
    monkeypatch.setenv("OAP_PRIVATE_SMI_ORIGIN", "https://smi.onanypostcode.global")
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
    auth_handoff = client.get("/auth?next=/mission/ollama")
    assert auth_handoff.status_code == 302
    assert auth_handoff.headers["Location"] == (
        "https://smi.onanypostcode.global/auth?next=/mission/ollama"
    )
    assert client.get("/the-spot/my-world").status_code == 404
    forged = client.get("/mission", headers={"X-OAP-SMI-Gateway": "x" * 48})
    assert forged.status_code == 404
    assert forged.headers["Cache-Control"] == "no-store"


@pytest.mark.parametrize("origin", [
    None,
    "",
    "https://oap-smi.onrender.com",
    "http://smi.onanypostcode.global",
    "https://onanypostcode.global",
    "https://user:secret@smi.onanypostcode.global",
    "https://smi.onanypostcode.global/private",
    "https://smi.onanypostcode.global?key=secret",
    "https://smi.onanypostcode.global:bad",
])
def test_public_private_handoff_fails_closed_without_verified_first_party_origin(monkeypatch, origin):
    monkeypatch.setenv("OAP_SURFACE_ROLE", "public")
    monkeypatch.setenv("OAP_SMI_GATEWAY_SECRET", "s" * 48)
    if origin is None:
        monkeypatch.delenv("OAP_PRIVATE_SMI_ORIGIN", raising=False)
    else:
        monkeypatch.setenv("OAP_PRIVATE_SMI_ORIGIN", origin)
    app = Flask(__name__)
    surface_security.register(app)
    client = app.test_client()
    for path in ("/smi", "/mission", "/mission/ollama", "/auth"):
        response = client.get(path)
        assert response.status_code == 404
        assert response.headers["Cache-Control"] == "no-store"
        assert "Location" not in response.headers


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
    monkeypatch.setenv("OAP_PRIVATE_SMI_ORIGIN", "https://smi.onanypostcode.global")
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
        "/auth": "/auth",
        "/enter-my-world": "/enter-my-world",
    }
    for source, target in expected.items():
        response = client.get(source)
        assert response.status_code == 302
        assert response.headers["Location"] == f"https://smi.onanypostcode.global{target}"

    auth_with_next = client.get("/enter-my-world?next=/global-affairs")
    assert auth_with_next.headers["Location"] == (
        "https://smi.onanypostcode.global/enter-my-world?next=/global-affairs"
    )


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
    assert (
        smi_gateway._allowed(
            "api/smi-organiser/connectivity-briefs/11111111-1111-4111-8111-111111111111"
        )
        is True
    )
    assert smi_gateway._allowed("api/smi-organiser-evil/connectivity-briefs") is False
    assert smi_gateway._allowed("on-any-place") is True
    assert smi_gateway._allowed("map-intelligence") is True
    assert smi_gateway._allowed("map-intelligence/route") is True
    assert smi_gateway._allowed("map-intelligence/road-geometry/14/8182/5455") is True
    assert smi_gateway._allowed("on-any-place/extra") is False
    assert smi_gateway._allowed("healthz") is True
    assert smi_gateway._allowed("assets/oap.css") is True
    assert smi_gateway._allowed("static/oap/smi_live_chat_dashboard.jpg") is True
    assert smi_gateway._allowed("static/oap/private-masks.zip") is False
    assert smi_gateway._allowed("static/oap/other-character.jpg") is False
    assert smi_gateway._allowed("static/oap/smi_live_chat_dashboard.jpg/extra") is False
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


def test_render_blueprint_keeps_public_and_smi_image_services_free():
    content = Path("render.yaml").read_text()
    assert "name: oap-smi" in content
    assert "name: on-any-postcode" in content
    assert content.count("runtime: image") == 2
    assert 'value: "smi_gateway:app"' in content
    assert 'value: "app:app"' in content
    assert content.count("plan: free") == 2
    assert "plan: starter" not in content
    assert "type: worker" not in content
    assert "name: oap-routing" not in content


def test_selfhost_defines_two_first_party_https_ingresses_without_host_exposed_smi():
    compose = Path("deploy/selfhost/compose.yaml").read_text()
    caddy = Path("deploy/selfhost/Caddyfile").read_text()
    assert "OAP_RUNTIME_TARGET: app:app" in compose
    assert "OAP_RUNTIME_TARGET: smi_gateway:app" in compose
    assert 'OAP_SMI_LOCAL_DISPATCH: "1"' in compose
    assert "OAP_PRIVATE_SMI_ORIGIN: https://" in compose
    assert "OAP_SMI_GATEWAY_SECRET:" in compose
    assert "OAP_SMI_DOMAIN:" in compose
    assert "{$OAP_DOMAIN}" in caddy
    assert "{$OAP_SMI_DOMAIN}" in caddy
    assert "reverse_proxy smi:10000" in caddy
    assert "reverse_proxy world:10000" in caddy
    assert '      - "10000:10000"' not in compose
    assert "onrender.com" not in compose + caddy


def test_smi_local_flask_launcher_is_loopback_only_and_preserves_auth():
    script = Path("scripts/smi_local_flask.sh").read_text()
    assert 'export OAP_SURFACE_ROLE=local' in script
    assert 'export OAP_SMI_GATEWAY_SECRET=' in script
    assert 'export OAP_AUTH_REQUIRED=true' in script
    assert 'route = "/mission/ollama"' in script
    assert 'SMI_FLASK_PREFLIGHT_404' in script
    assert 'host="127.0.0.1", port=5051, debug=False, use_reloader=False' in script
    assert 'app.test_client()' in script
    assert "auto-login" in script
    assert "OAP_SURFACE_ROLE=public" not in script
    assert 'home_env="$HOME/.config/oap/home-node.env"' in script
    assert 'founder_env="$HOME/.config/oap/smi-founder.env"' in script
    assert 'SMI_FLASK_FOUNDER_CONFIG_PERMISSIONS' in script
    assert 'SMI NEXT ACTION:' in script
    assert 'chmod 600' in script
    assert 'NEON_AUTH_BASE_URL=' not in script
    assert 'OAP_HUMAN_AUTHORITY_EMAIL=' not in script

    assert 'SMI_FLASK_AUTH_NOT_CONFIGURED' in script
    assert 'SMI Founder verifier:' in script
    assert 'connection unverified' in script
    assert 'founder_local_auth.bound()' in script
    assert 'local_verifier_bound' in script
    assert 'if not (managed_ready or local_verifier_bound or recovery_ready):' in script
    assert 'OAP_SESSION_SECRET' in script
