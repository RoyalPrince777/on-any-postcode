"""Founder-gated invitation control must not issue invitations prematurely."""


def test_invitation_control_requires_authentication(anonymous_client):
    response = anonymous_client.get(
        "/begoro-koradaso/invitations/control", follow_redirects=False
    )
    assert response.status_code in (302, 303, 401, 403)
    assert "issuance disabled" not in response.get_data(as_text=True)


def test_non_authority_denied_invitation_control(client, monkeypatch):
    from mission_control import web_security

    monkeypatch.setattr(web_security, "private_authority_allowed", lambda user: False)
    response = client.get("/begoro-koradaso/invitations/control")
    assert response.status_code == 403


def test_authority_sees_hold_without_issue_action(client, monkeypatch):
    from mission_control import web_security

    monkeypatch.setattr(web_security, "private_authority_allowed", lambda user: True)
    response = client.get("/begoro-koradaso/invitations/control")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "issuance disabled" in body
    assert "<form" not in body.lower()
    assert response.headers["Cache-Control"] == "private, no-store"
    assert response.headers["X-Robots-Tag"] == "noindex, nofollow, noarchive"
