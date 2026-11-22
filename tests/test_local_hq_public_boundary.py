"""Public discovery cannot render account/HQ routes, even with trusted headers."""
import pytest

import app as app_module
from mission_control import web_security


@pytest.fixture
def local_public(monkeypatch):
    monkeypatch.setitem(app_module.app.config, "OAP_LOCAL_SERVICE_ROLE", "public")
    monkeypatch.setenv("OAP_SMI_GATEWAY_SECRET", "g" * 40)


def test_public_discovery_stays_available(anonymous_client, local_public):
    for path in ("/world", "/store", "/pay/bank", "/oap-store/apps"):
        assert anonymous_client.get(path).status_code == 200


@pytest.mark.parametrize("path", [
    "/pay/bank/me/status", "/pay/bank/me/activity", "/pay/bank/control-center",
    "/pay/bank/founder/provision", "/mission/brain/status", "/internal/eiot/persistence/save",
    "/api/global-affairs/recovery/record",
])
def test_public_cannot_render_or_execute_private_routes(client, local_public, monkeypatch, path):
    monkeypatch.setattr(web_security, "private_authority_allowed", lambda user: True)
    for method in ("GET", "POST"):
        response = client.open(path, method=method, headers={
            "X-OAP-SMI-Gateway": "g" * 40,
            "X-Forwarded-Host": "127.0.0.1:5000",
            "X-Forwarded-Port": "5000",
        })
        assert response.status_code == 404
        assert response.headers["Cache-Control"] == "no-store"


def test_public_account_and_sign_in_doors_hand_off_without_host_or_query_injection(
    anonymous_client, local_public,
):
    for path in ("/pay/bank/me", "/my-world", "/auth"):
        response = anonymous_client.get(path + "?next=https://example.test/", headers={"Host": "example.test:5000"})
        assert response.status_code == 302
        assert response.headers["Location"] == "http://127.0.0.1:5000" + path
        assert response.headers["Cache-Control"] == "no-store"
        assert anonymous_client.post(path, data={"password": "unused"}).status_code == 404


def test_hq_requires_sign_in(anonymous_client, monkeypatch):
    monkeypatch.setitem(app_module.app.config, "OAP_LOCAL_SERVICE_ROLE", "hq")
    assert anonymous_client.get("/").headers["Location"] == "/mission/smi"
    for path in ("/pay/bank/me", "/pay/bank/control-center"):
        response = anonymous_client.get(path)
        assert response.status_code == 302
        assert "/enter-my-world" in response.headers["Location"]
        assert response.headers["Cache-Control"] == "no-store"


def test_hq_retains_founder_authority(client, monkeypatch):
    monkeypatch.setitem(app_module.app.config, "OAP_LOCAL_SERVICE_ROLE", "hq")
    monkeypatch.setattr(web_security, "private_authority_allowed", lambda user: False)
    assert client.get("/pay/bank/control-center").status_code == 403
    monkeypatch.setattr(web_security, "private_authority_allowed", lambda user: True)
    response = client.get("/pay/bank/control-center")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
