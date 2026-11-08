import pytest

from mission_control import oware


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


@pytest.mark.parametrize("level", ["beginner", "standard", "expert"])
def test_oware_agent_replies_once_and_game_can_resume_or_restart(client, csrf, level):
    headers = {"X-OAP-CSRF": csrf["csrf_token"]}
    started = client.post("/arena/oware/start", json={"agent_level": level}, headers=headers).get_json()
    move = {"pit": 0, "game_id": started["game_id"], "request_id": "oware-agent-test-001"}
    response = client.post("/arena/oware/move", json=move, headers=headers)
    assert response.status_code == 200
    played = response.get_json()
    assert played["agent_level"] == level
    assert played["current_player_id"] == "p1"
    assert played["last_pit"] in range(6, 12)
    assert sum(played["pits"]) + sum(player["captured"] for player in played["players"]) == 48
    with client.session_transaction() as session:
        assert len(session[oware.SESSION_KEY]["request_receipts"]) == 2
    assert client.post("/arena/oware/move", json=move, headers=headers).get_json() == played
    assert client.get("/arena/oware/state").get_json() == played

    restarted = client.post("/arena/oware/start", json={}, headers=headers).get_json()
    assert restarted["game_id"] != started["game_id"]
    assert restarted["agent_level"] is None
    assert restarted["pits"] == [4] * 12
    assert client.post("/arena/oware/move", json=move, headers=headers).get_json()["error"]["code"] == "oware_game_changed"
