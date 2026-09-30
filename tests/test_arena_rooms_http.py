from __future__ import annotations


def test_arena_room_http_flow(client, csrf, monkeypatch):
    import app as app_module

    created = {
        "room_id": "00000000-0000-0000-0000-000000000001",
        "room_code": "ABC234",
        "player_id": "00000000-0000-0000-0000-000000000002",
        "reconnect_token": "host-token-" + "x" * 32,
        "game_key": "connect4",
        "capacity": 2,
        "status": "WAITING",
        "revision": 0,
    }

    monkeypatch.setattr(app_module.arena_rooms, "create_room", lambda **kwargs: created)
    monkeypatch.setattr(
        app_module.arena_rooms,
        "join_room",
        lambda **kwargs: {
            "room_id": created["room_id"],
            "room_code": created["room_code"],
            "player_id": "00000000-0000-0000-0000-000000000003",
            "reconnect_token": "guest-token-" + "y" * 32,
            "game_key": "connect4",
            "seat": 2,
        },
    )
    monkeypatch.setattr(
        app_module.arena_rooms,
        "room_state",
        lambda **kwargs: {
            "room_id": created["room_id"],
            "room_code": created["room_code"],
            "game_key": "connect4",
            "status": "ACTIVE",
            "capacity": 2,
            "revision": 1,
            "game_state": {"turn": "p1"},
            "players": [{"display_name": "Alpha", "seat": 1}, {"display_name": "Bravo", "seat": 2}],
            "chat": False,
            "payments": False,
        },
    )
    monkeypatch.setattr(
        app_module.arena_rooms,
        "update_game_state",
        lambda **kwargs: {"room_id": created["room_id"], "revision": 2, "duplicate": False},
    )

    headers = {"X-OAP-CSRF": csrf["csrf_token"]}
    assert client.post("/arena/rooms/create", json={"game_key": "connect4", "host_name": "Alpha", "capacity": 2}).status_code == 403

    response = client.post(
        "/arena/rooms/create",
        json={"game_key": "connect4", "host_name": "Alpha", "capacity": 2},
        headers=headers,
    )
    assert response.status_code == 201
    assert response.get_json()["room_code"] == "ABC234"

    joined = client.post(
        "/arena/rooms/join",
        json={"room_code": "ABC234", "display_name": "Bravo"},
        headers=headers,
    )
    assert joined.status_code == 201
    assert joined.get_json()["seat"] == 2

    state = client.post(
        "/arena/rooms/state",
        json={"room_id": created["room_id"], "reconnect_token": created["reconnect_token"]},
        headers=headers,
    )
    assert state.status_code == 200
    assert state.get_json()["chat"] is False

    updated = client.post(
        "/arena/rooms/state/update",
        json={
            "room_id": created["room_id"],
            "reconnect_token": created["reconnect_token"],
            "expected_revision": 1,
            "game_state": {"turn": "p2"},
            "request_id": "room-http-0001",
        },
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.get_json()["revision"] == 2
