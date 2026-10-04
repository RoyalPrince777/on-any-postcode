from __future__ import annotations


def test_arena_hub_surfaces_my_card_and_all_proven_room_modes(anonymous_client):
    response = anonymous_client.get("/arena")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'href="/my-card"' in page
    assert "My Card" in page
    for room_path in (
        "/arena/connect4/room",
        "/arena/dot/room",
        "/arena/chess/room",
        "/arena/ludo/room",
        "/arena/oware/room",
    ):
        assert f'href="{room_path}"' in page
    assert "Create / Join Chess Room" in page
    assert "My Card history" in page


def test_my_card_is_canonical_arena_identity_door(anonymous_client):
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


def test_arena_truth_copy_distinguishes_challenge_boundary_from_wider_foundations(anonymous_client):
    response = anonymous_client.get("/arena")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Challenge Engine remains session-scoped and non-ranked" in page
    assert "multiplayer rooms are exposed for Connect 4, Dot, Chess, Ludo and Oware" in page
    assert "durable player-profile and ranking foundations exist behind explicit migration" in page
    assert "Multiplayer, durable profiles, rankings, payments, prizes" not in page


def test_arena_product_registry_no_longer_claims_all_multiplayer_locked():
    from mission_control import products

    arena = next(item for item in products.SPOT_CAPABILITIES if item["id"] == "arena")
    assert "Connect 4, Dot, Chess, Ludo and Oware room multiplayer exposed" in arena["status"]
    assert "remaining iq arena and route empire room exposure" in arena["blocked_by"].lower()
    assert "Durable profiles, multiplayer, rankings" not in arena["blocked_by"]
