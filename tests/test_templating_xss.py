from __future__ import annotations

import mission_control.status as mission_status


def test_legacy_user_content_is_escaped(client):
    attack = '<script>alert("legacy")</script>'
    client.post("/signal", data={"name": attack, "body": attack})

    page = client.get("/").get_data(as_text=True)

    assert attack not in page
    assert "&lt;script&gt;alert" in page


def test_gateway_status_content_is_escaped(client, monkeypatch):
    payload = mission_status.get_public_gateway_status()
    attack = '<img src=x onerror="alert(1)">'
    payload["components"][0]["value"] = attack
    payload["agents"][0]["assignment"] = attack
    payload["approval_summary"]["message"] = attack
    monkeypatch.setattr(
        mission_status,
        "get_public_gateway_status",
        lambda: payload,
    )

    page = client.get("/").get_data(as_text=True)

    assert attack not in page
    assert "&lt;img src=x onerror=" in page
    assert page.count("&lt;img src=x onerror=") == 3
