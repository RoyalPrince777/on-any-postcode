import importlib


def test_smi_gateway_forwards_render_client_ip(monkeypatch):
    gateway = importlib.import_module("smi_gateway")
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("OAP_SMI_GATEWAY_SECRET", "s" * 64)

    with gateway.app.test_request_context(
        "/auth",
        headers={
            "X-Forwarded-For": "203.0.113.42, 10.0.0.2",
            "X-OAP-Client-IP": "198.51.100.9",
        },
        environ_base={"REMOTE_ADDR": "10.0.0.5"},
    ):
        headers = gateway._request_headers()

    assert headers["X-OAP-SMI-Gateway"] == "s" * 64
    assert headers["X-OAP-Client-IP"] == "203.0.113.42"


def test_smi_gateway_rejects_invalid_forwarded_ip(monkeypatch):
    gateway = importlib.import_module("smi_gateway")
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("OAP_SMI_GATEWAY_SECRET", "s" * 64)

    with gateway.app.test_request_context(
        "/auth",
        headers={"X-Forwarded-For": "not-an-ip"},
        environ_base={"REMOTE_ADDR": "10.0.0.5"},
    ):
        assert gateway._request_headers()["X-OAP-Client-IP"] == "unknown"


def test_authorized_gateway_restores_client_ip_before_founder_limiter(monkeypatch):
    oap = importlib.import_module("app")
    secret = "g" * 64
    monkeypatch.setenv("OAP_SMI_GATEWAY_SECRET", secret)
    monkeypatch.setenv("OAP_SURFACE_ROLE", "public")

    with oap.app.test_request_context(
        "/auth",
        headers={
            "X-OAP-SMI-Gateway": secret,
            "X-OAP-Client-IP": "203.0.113.77",
        },
        environ_base={"REMOTE_ADDR": "10.0.0.8"},
    ):
        response = oap.app.preprocess_request()
        assert response is None
        assert oap._auth_rate_key() == "auth:sign-in:203.0.113.77"


def test_untrusted_client_ip_header_cannot_change_rate_key(monkeypatch):
    oap = importlib.import_module("app")
    secret = "g" * 64
    monkeypatch.setenv("OAP_SMI_GATEWAY_SECRET", secret)
    monkeypatch.setenv("OAP_SURFACE_ROLE", "public")

    with oap.app.test_request_context(
        "/auth",
        headers={
            "X-OAP-SMI-Gateway": "x" * 64,
            "X-OAP-Client-IP": "203.0.113.99",
        },
        environ_base={"REMOTE_ADDR": "10.0.0.9"},
    ):
        response = oap.app.preprocess_request()
        assert response is not None
        assert response.status_code == 404
        assert oap._auth_rate_key() == "auth:sign-in:10.0.0.9"
