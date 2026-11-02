"""Opt-in Shere Khan AI uses the existing server-authoritative Ludo engine."""


def test_ludo_shere_khan_opt_in_turn_and_human_boundary(client, csrf):
    headers = {"X-OAP-CSRF": csrf["csrf_token"]}
    start = client.post(
        "/arena/ludo/start",
        json={"players": ["You", "Shere Khan"], "opponent": "shere-khan", "level": "cub"},
        headers=headers,
    )
    assert start.status_code == 201
    assert start.get_json()["current_player_id"] == "p1"

    # Ensure an AI turn without waiting for random die rolls.
    with client.session_transaction() as session:
        from mission_control import ludo

        state = session[ludo.SESSION_KEY]
        state["turn_index"] = 1
        session[ludo.SESSION_KEY] = ludo._seal(state)

    manual = client.post(
        "/arena/ludo/roll", json={"request_id": "manual-turn-0001"}, headers=headers
    )
    assert manual.status_code == 400

    automatic = client.post(
        "/arena/ludo/shere-khan/turn",
        json={"request_id": "agent-turn-0001"},
        headers=headers,
    )
    assert automatic.status_code == 200
    assert automatic.get_json()["status"] == "active"
    with client.session_transaction() as session:
        before_retry = session[ludo.SESSION_KEY]
    repeat = client.post(
        "/arena/ludo/shere-khan/turn",
        json={"request_id": "agent-turn-0001"},
        headers=headers,
    )
    assert repeat.status_code == 200
    assert repeat.get_json() == automatic.get_json()
    with client.session_transaction() as session:
        assert session[ludo.SESSION_KEY] == before_retry


def test_ludo_agent_requires_opt_in(client, csrf):
    headers = {"X-OAP-CSRF": csrf["csrf_token"]}
    started = client.post(
        "/arena/ludo/start",
        json={"players": ["Alpha", "Bravo"]},
        headers=headers,
    )
    assert started.status_code == 201
    denied = client.post(
        "/arena/ludo/shere-khan/turn",
        json={"request_id": "agent-turn-0002"},
        headers=headers,
    )
    assert denied.status_code == 400
