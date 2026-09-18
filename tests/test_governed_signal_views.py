from __future__ import annotations


def test_governed_signal_endpoint_is_registered_as_post_only(client):
    rule = next(
        rule
        for rule in client.application.url_map.iter_rules()
        if rule.rule == "/mission/smi/governed-signal"
    )

    assert "POST" in rule.methods
    assert "GET" not in rule.methods


def test_governed_signal_endpoint_fails_closed_for_anonymous_user(client):
    response = client.post(
        "/mission/smi/governed-signal",
        json={"content": "Review this Signal", "requested_action": "review"},
    )

    assert response.status_code in {302, 401, 403, 404}
