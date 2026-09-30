def test_oware_arena_route_and_governed_moves(client, csrf):
    page = client.get("/arena/oware")
    assert page.status_code == 200
    text = page.get_data(as_text=True)
    assert "Oware" in text
    assert "48 seeds" in text
    assert "/static/oware.js" in text

    headers = {"X-OAP-CSRF": csrf["csrf_token"]}
    started = client.post(
        "/arena/oware/start",
        json={"players": ["Ama", "Kojo"]},
        headers=headers,
    )
    assert started.status_code == 201
    body = started.get_json()
    assert body["pits"] == [4] * 12
    assert body["current_player_name"] == "Ama"
    assert body["legal_pits"] == [0, 1, 2, 3, 4, 5]

    moved = client.post(
        "/arena/oware/move",
        json={"pit": 0, "request_id": "http-oware-0001"},
        headers=headers,
    )
    assert moved.status_code == 200
    moved_body = moved.get_json()
    assert moved_body["current_player_name"] == "Kojo"
    assert sum(moved_body["pits"]) + sum(
        player["captured"] for player in moved_body["players"]
    ) == 48


def test_arena_front_door_lists_oware(client):
    page = client.get("/arena")
    assert page.status_code == 200
    text = page.get_data(as_text=True)
    assert "🌰 Oware" in text
    assert 'href="/arena/oware"' in text
