"""Public Begoro × KORADASO opportunity discovery remains read-only."""


def test_public_opportunities_page_is_visible_without_login(anonymous_client):
    response = anonymous_client.get("/begoro-koradaso/opportunities")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Begoro × KORADASO" in body
    assert "Invite-only to participate" in body
    assert "no public sign-up" in body.lower() or "no public sign-up" in body
    assert response.headers["Content-Security-Policy"]
    assert response.headers["X-Robots-Tag"] == "noindex, nofollow"


def test_public_page_has_no_active_enrollment_or_checkout(anonymous_client):
    response = anonymous_client.get("/begoro-koradaso/opportunities")
    body = response.get_data(as_text=True).lower()
    assert "<form" not in body
    assert "type=\"submit\"" not in body
    assert "private heritage" not in body
    assert "no earnings are guaranteed" in body
