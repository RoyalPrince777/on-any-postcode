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
            "your_seat": 1,
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
    assert updated.status_code == 400
    assert updated.get_json()["error"]["code"] == "arena_room_server_game_adapter_required"


def test_connect4_room_action_http_csrf_and_adapter(client, csrf, monkeypatch):
    import app as app_module

    expected_room = "00000000-0000-0000-0000-000000000001"

    def fake_action(**kwargs):
        assert kwargs["room_id"] == expected_room
        assert kwargs["action"] == "drop"
        assert kwargs["column"] == 3
        assert kwargs["expected_revision"] == 0
        return {"room_id": expected_room, "revision": 1, "duplicate": False, "status": "ACTIVE"}

    monkeypatch.setattr(app_module.arena_rooms, "connect4_action", fake_action)
    payload = {
        "room_id": expected_room,
        "reconnect_token": "x" * 40,
        "expected_revision": 0,
        "request_id": "http-room-c4-0001",
        "action": "drop",
        "column": 3,
    }
    assert client.post("/arena/rooms/connect4/action", json=payload).status_code == 403
    response = client.post(
        "/arena/rooms/connect4/action",
        json=payload,
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )
    assert response.status_code == 200
    assert response.get_json()["revision"] == 1


def test_connect4_room_page_has_create_join_reconnect_and_control_paths(client):
    page = client.get("/arena/connect4/room")
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    assert "arena_connect4_room.js" in html
    assert "data-create" in html
    assert "data-join" in html
    assert "data-reconnect" in html
    assert "data-columns" in html
    assert "data-refresh" in html
    assert "data-stop" in html
    assert "data-reconnect-seat" not in html
    assert page.headers["Referrer-Policy"] == "no-referrer"



def test_dot_room_page_and_authoritative_http_action(client, csrf, monkeypatch):
    import app as app_module

    page = client.get("/arena/dot/room")
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    assert "arena_dot_room.js" in html
    for action in ("data-create", "data-join", "data-reconnect", "data-edges", "data-refresh", "data-stop"):
        assert action in html
    assert "data-reconnect-seat" not in html
    assert page.headers["Referrer-Policy"] == "no-referrer"

    expected_room = "00000000-0000-0000-0000-000000000001"

    def fake_dot_action(**kwargs):
        assert kwargs["room_id"] == expected_room
        assert kwargs["action"] == "draw"
        assert (kwargs["a"], kwargs["b"]) == ("0,0", "1,0")
        assert kwargs["expected_revision"] == 0
        return {"room_id": expected_room, "revision": 1, "duplicate": False, "status": "ACTIVE"}

    monkeypatch.setattr(app_module.arena_rooms, "dot_action", fake_dot_action)
    payload = {
        "room_id": expected_room,
        "reconnect_token": "x" * 40,
        "expected_revision": 0,
        "request_id": "http-dot-room-0001",
        "action": "draw",
        "a": "0,0",
        "b": "1,0",
    }
    assert client.post("/arena/rooms/dot/action", json=payload).status_code == 403
    response = client.post(
        "/arena/rooms/dot/action",
        json=payload,
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )
    assert response.status_code == 200
    assert response.get_json()["revision"] == 1


def test_multiplayer_clients_serialize_entry_and_fail_closed_on_uncertain_moves(client):
    for route, asset, root in (
        ("/arena/connect4/room", "/static/arena_connect4_room.js", "data-room-root"),
        ("/arena/dot/room", "/static/arena_dot_room.js", "data-dot-room"),
    ):
        page = client.get(route)
        assert page.status_code == 200
        assert root in page.get_data(as_text=True)
        response = client.get(asset)
        assert response.status_code == 200
        js = response.get_data(as_text=True)
        assert "entryBusy" in js
        assert "needsRefresh" in js
        assert "refreshInFlight" in js
        assert "async function enter(task)" in js
        assert "if(entryBusy||busy)return;" in js
        assert "if(busy||needsRefresh" in js
        assert "if(membership!==current)return;" in js or "if(me!==current)return;" in js
        assert "Retry Refresh before" in js or "Refresh before another action" in js
        assert 'q("[data-refresh]").disabled=true' in js



def test_ludo_and_oware_room_pages_and_actions(client, csrf, monkeypatch):
    import app as app_module

    for route, asset, root in (
        ("/arena/ludo/room", "arena_ludo_room.js", "data-ludo-room"),
        ("/arena/oware/room", "arena_oware_room.js", "data-oware-room"),
    ):
        page = client.get(route)
        html = page.get_data(as_text=True)
        assert page.status_code == 200
        assert asset in html
        assert root in html
        for marker in ("data-create", "data-join", "data-reconnect", "data-refresh", "data-stop"):
            assert marker in html
        assert page.headers["Referrer-Policy"] == "no-referrer"

    expected_room = "00000000-0000-0000-0000-000000000001"
    monkeypatch.setattr(
        app_module.arena_rooms,
        "ludo_action",
        lambda **kwargs: {
            "room_id": expected_room, "revision": 1, "duplicate": False,
            "status": "ACTIVE", "game_state": {"pending_roll": 4},
        },
    )
    ludo_payload = {
        "room_id": expected_room, "reconnect_token": "x" * 40,
        "expected_revision": 0, "request_id": "http-ludo-room-0001",
        "action": "roll",
    }
    assert client.post("/arena/rooms/ludo/action", json=ludo_payload).status_code == 403
    response = client.post(
        "/arena/rooms/ludo/action", json=ludo_payload,
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )
    assert response.status_code == 200
    assert response.get_json()["revision"] == 1

    monkeypatch.setattr(
        app_module.arena_rooms,
        "oware_action",
        lambda **kwargs: {
            "room_id": expected_room, "revision": 1, "duplicate": False,
            "status": "ACTIVE", "game_state": {"pits": [0, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 4]},
        },
    )
    oware_payload = {
        "room_id": expected_room, "reconnect_token": "x" * 40,
        "expected_revision": 0, "request_id": "http-oware-room-0001",
        "action": "move", "pit": 0,
    }
    assert client.post("/arena/rooms/oware/action", json=oware_payload).status_code == 403
    response = client.post(
        "/arena/rooms/oware/action", json=oware_payload,
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )
    assert response.status_code == 200
    assert response.get_json()["revision"] == 1



def test_iq_and_route_empire_room_pages_and_actions(client, csrf, monkeypatch):
    import app as app_module

    for route, asset, root in (
        ("/arena/iq/room", "arena_iq_room.js", "data-iq-room"),
        ("/arena/route-empire/room", "arena_route_empire_room.js", "data-route-room"),
    ):
        page = client.get(route)
        html = page.get_data(as_text=True)
        assert page.status_code == 200
        assert asset in html
        assert root in html
        for marker in ("data-create", "data-join", "data-reconnect", "data-refresh", "data-stop"):
            assert marker in html
        assert page.headers["Referrer-Policy"] == "no-referrer"

    expected_room = "00000000-0000-0000-0000-000000000001"
    monkeypatch.setattr(
        app_module.arena_rooms,
        "iq_action",
        lambda **kwargs: {
            "room_id": expected_room, "revision": 1, "duplicate": False,
            "status": "ACTIVE", "game_state": {"your_answer_locked": True},
        },
    )
    iq_payload = {
        "room_id": expected_room, "reconnect_token": "x" * 40,
        "expected_revision": 0, "request_id": "http-iq-room-0001",
        "action": "answer", "choice_id": "b",
    }
    assert client.post("/arena/rooms/iq/action", json=iq_payload).status_code == 403
    response = client.post(
        "/arena/rooms/iq/action", json=iq_payload,
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )
    assert response.status_code == 200
    assert response.get_json()["revision"] == 1

    monkeypatch.setattr(
        app_module.arena_rooms,
        "route_empire_action",
        lambda **kwargs: {
            "room_id": expected_room, "revision": 1, "duplicate": False,
            "status": "ACTIVE", "game_state": {"round": 1},
        },
    )
    route_payload = {
        "room_id": expected_room, "reconnect_token": "x" * 40,
        "expected_revision": 0, "request_id": "http-route-room-0001",
        "action": "claim", "node_id": "north",
    }
    assert client.post("/arena/rooms/route-empire/action", json=route_payload).status_code == 403
    response = client.post(
        "/arena/rooms/route-empire/action", json=route_payload,
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )
    assert response.status_code == 200
    assert response.get_json()["revision"] == 1



def test_matchmaking_http_requires_csrf_and_returns_membership(client, csrf, monkeypatch):
    import app as app_module

    result = {
        "room_id": "00000000-0000-0000-0000-000000000010",
        "room_code": "ABC234",
        "player_id": "00000000-0000-0000-0000-000000000011",
        "reconnect_token": "match-token-" + "x" * 32,
        "game_key": "chess",
        "seat": 1,
        "status": "WAITING",
        "matched": False,
        "matchmaking": True,
    }
    monkeypatch.setattr(app_module.arena_rooms, "matchmake", lambda **kwargs: result)

    payload = {"game_key": "chess", "display_name": "Alpha"}
    assert client.post("/arena/rooms/matchmake", json=payload).status_code == 403
    response = client.post(
        "/arena/rooms/matchmake",
        json=payload,
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )
    assert response.status_code == 201
    assert response.get_json()["matchmaking"] is True
    assert response.get_json()["game_key"] == "chess"


def test_all_authoritative_room_games_expose_quick_match(client):
    cases = (
        ("/arena/connect4/room", "/static/arena_connect4_room.js", "connect4"),
        ("/arena/dot/room", "/static/arena_dot_room.js", "dot"),
        ("/arena/chess/room", "/static/arena_chess_room.js", "chess"),
        ("/arena/ludo/room", "/static/arena_ludo_room.js", "ludo"),
        ("/arena/oware/room", "/static/arena_oware_room.js", "oware"),
        ("/arena/iq/room", "/static/arena_iq_room.js", "iq"),
        ("/arena/route-empire/room", "/static/arena_route_empire_room.js", "route-empire"),
    )
    for page_path, asset_path, game_key in cases:
        page = client.get(page_path)
        assert page.status_code == 200
        assert "data-matchmake" in page.get_data(as_text=True)
        script = client.get(asset_path)
        assert script.status_code == 200
        text = script.get_data(as_text=True)
        assert "/arena/rooms/matchmake" in text
        assert f'game_key:"{game_key}"' in text
