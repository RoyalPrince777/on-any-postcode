from __future__ import annotations

import smi_gateway


def test_smi_gateway_exposes_local_civilization_status():
    client = smi_gateway.app.test_client()
    response = client.get("/mission/civilization")
    assert response.status_code == 200
    assert response.headers["X-OAP-Civilization-Source"] == "local-smi-runtime"
    payload = response.get_json()
    assert payload["name"] == "OAP Living Digital Civilization System"
    assert payload["operational_green"] is False
    assert payload["validation"]["passed"] is True
