def test_ludo_page_exposes_classic_four_token_rules(client):
    page = client.get("/arena/ludo")
    text = page.get_data(as_text=True)
    assert page.status_code == 200
    assert "Bring all four home" in text
    assert "six to leave the yard" in text
    assert 'data-roll' in text
    assert 'data-step=' not in text


def test_ludo_http_roll_and_move_piece(client, csrf, monkeypatch):
    from mission_control import ludo

    headers = {"X-OAP-CSRF": csrf["csrf_token"]}
    started = client.post(
        "/arena/ludo/start",
        json={"players": ["Alpha", "Bravo"]},
        headers=headers,
    )
    assert started.status_code == 201
    assert started.get_json()["players"][0]["pieces"] == [-1, -1, -1, -1]

    monkeypatch.setattr(ludo.secrets, "randbelow", lambda _: 5)
    rolled = client.post(
        "/arena/ludo/roll",
        json={"request_id": "http-ludo-roll-0001"},
        headers=headers,
    )
    assert rolled.status_code == 200
    assert rolled.get_json()["die"] == 6
    assert rolled.get_json()["legal_pieces"] == [0, 1, 2, 3]

    moved = client.post(
        "/arena/ludo/move",
        json={"piece_index": 0, "request_id": "http-ludo-move-0001"},
        headers=headers,
    )
    assert moved.status_code == 200
    assert moved.get_json()["players"][0]["pieces"][0] == 0
    assert moved.get_json()["current_player_name"] == "Alpha"
