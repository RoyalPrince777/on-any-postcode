from __future__ import annotations


def test_my_card_links_to_oap_arena(anonymous_client):
    with anonymous_client.session_transaction() as current_session:
        current_session["oap_public_my_card"] = {
            "identity_id": "55555555-5555-4555-8555-555555555555",
            "card_id": "OAP-55555555",
            "display_name": "Arena Member",
            "credentialed": False,
        }

    response = anonymous_client.get("/my-card")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'href="/arena"' in page
    assert "OAP Arena" in page
    assert "carry your Arena record on this My Card" in page


def test_arena_uses_my_card_as_user_facing_identity_surface(anonymous_client):
    response = anonymous_client.get("/arena")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'href="/my-card"' in page
    assert ">My Card</a>" in page
    assert "My Card history" in page
    assert "Durable player history" not in page
