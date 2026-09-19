from flask import Flask, request
from werkzeug.test import Client
from werkzeug.wrappers import Response as WerkzeugResponse

import smi_gateway


def _configure(monkeypatch):
    monkeypatch.setenv("OAP_SMI_GATEWAY_SECRET", "g" * 64)
    monkeypatch.setenv("OAP_SMI_LOCAL_DISPATCH", "true")
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("OAP_A6_READINESS_ON_HEALTH", raising=False)
    monkeypatch.delenv("OAP_A6_ROUTE_MATRIX_ON_HEALTH", raising=False)


def test_private_auth_dispatches_in_process_without_upstream_http(monkeypatch):
    _configure(monkeypatch)
    core = Flask("fake-core")

    @core.get("/auth")
    def auth():
        assert request.headers["X-OAP-SMI-Gateway"] == "g" * 64
        return "local-auth", 200

    monkeypatch.setattr(smi_gateway, "_core_wsgi_app", lambda: core.wsgi_app)

    class _ExplodingOpener:
        def open(self, *_args, **_kwargs):
            raise AssertionError("public Render edge must not be used")

    monkeypatch.setattr(smi_gateway, "_OPENER", _ExplodingOpener())

    client = Client(smi_gateway.app, WerkzeugResponse)
    response = client.get("/auth?next=/mission/ollama")

    assert response.status_code == 200
    assert response.get_data(as_text=True) == "local-auth"
    assert response.headers["X-OAP-Dispatch"] == "local-process"
    assert response.headers["X-OAP-Request-ID"]


def test_gateway_health_stays_gateway_owned_in_local_mode(monkeypatch):
    _configure(monkeypatch)

    def _should_not_load_core():
        raise AssertionError("health must remain gateway-owned")

    monkeypatch.setattr(smi_gateway, "_core_wsgi_app", _should_not_load_core)
    client = Client(smi_gateway.app, WerkzeugResponse)

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json["service"] == "oap-smi-gateway"
    assert response.json["private_dispatch"] == "local-process"


def test_local_mode_keeps_non_allowlisted_surface_closed(monkeypatch):
    _configure(monkeypatch)

    def _should_not_load_core():
        raise AssertionError("disallowed paths must not reach the core app")

    monkeypatch.setattr(smi_gateway, "_core_wsgi_app", _should_not_load_core)
    client = Client(smi_gateway.app, WerkzeugResponse)

    response = client.get("/not-an-oap-private-route")

    assert response.status_code == 404
