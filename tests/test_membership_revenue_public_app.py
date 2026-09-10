def test_membership_money_surface_is_public_and_does_not_grant_private_access(anonymous_client):
    page = anonymous_client.get("/membership")
    status = anonymous_client.get("/membership/status")

    assert page.status_code == 200
    assert status.status_code == 200
    text = page.get_data(as_text=True)
    assert "OAP Membership" in text
    assert "Public OAP stays open" in text
    assert "never grants Human Authority" in text
    assert "Mission Control" in text
    assert status.get_json()["founder_authority_granted"] is False


def test_existing_spot_membership_card_is_the_money_surface(anonymous_client):
    response = anonymous_client.get("/the-spot/membership")
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert "OAP Membership" in text
    assert "Postcode Founder" in text
    assert "£5 / month" in text
    assert "never grants Human Authority" in text


def test_unknown_membership_tier_is_not_an_open_redirect(anonymous_client):
    response = anonymous_client.get("/membership/checkout/not-a-tier")

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "membership_tier_not_found"
