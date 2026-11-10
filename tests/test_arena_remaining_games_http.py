from mission_control import ludo


def test_remaining_arena_game_routes(client, csrf, monkeypatch):
    for path, label in (
        ("/arena/ludo", "Ludo"),
        ("/arena/chess", "Chess"),
        ("/arena/dot", "Dot"),
    ):
        response = client.get(path)
        assert response.status_code == 200
        assert label in response.get_data(as_text=True)

    headers = {"X-OAP-CSRF": csrf["csrf_token"]}

    ludo_started = client.post(
        "/arena/ludo/start",
        json={"players": ["Alpha", "Bravo"]},
        headers=headers,
    )
    assert ludo_started.status_code == 201
    assert ludo_started.get_json()["current_player_name"] == "Alpha"
    assert len(ludo_started.get_json()["players"][0]["pieces"]) == 4

    monkeypatch.setattr(ludo.secrets, "randbelow", lambda _: 5)
    ludo_rolled = client.post(
        "/arena/ludo/roll",
        json={"request_id": "http-ludo-roll-0001"},
        headers=headers,
    )
    assert ludo_rolled.status_code == 200
    assert ludo_rolled.get_json()["pending_roll"] == 6
    assert "p1-1" in ludo_rolled.get_json()["movable_piece_ids"]

    ludo_moved = client.post(
        "/arena/ludo/move",
        json={"piece_id": "p1-1", "request_id": "http-ludo-move-0001"},
        headers=headers,
    )
    assert ludo_moved.status_code == 200
    assert ludo_moved.get_json()["players"][0]["pieces"][0]["zone"] == "track"

    chess_started = client.post("/arena/chess/start", json={}, headers=headers)
    assert chess_started.status_code == 201
    chess_moved = client.post(
        "/arena/chess/move",
        json={"source": "e2", "target": "e4", "request_id": "http-chess-0001"},
        headers=headers,
    )
    assert chess_moved.status_code == 200
    assert chess_moved.get_json()["board"]["e4"] == "wP"

    chess_resigned = client.post(
        "/arena/chess/resign",
        json={"request_id": "http-chess-resign-0001"},
        headers=headers,
    )
    assert chess_resigned.status_code == 200
    assert chess_resigned.get_json()["status"] == "completed"
    assert chess_resigned.get_json()["result"] == "resignation"
    assert chess_resigned.get_json()["winner"] == "White"

    dot_started = client.post("/arena/dot/start", json={}, headers=headers)
    assert dot_started.status_code == 201
    dot_drawn = client.post(
        "/arena/dot/draw",
        json={"a": "0,0", "b": "1,0", "request_id": "http-dot-0001"},
        headers=headers,
    )
    assert dot_drawn.status_code == 200
    assert ["0,0", "1,0"] in dot_drawn.get_json()["edges"]
