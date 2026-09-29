from mission_control import route_empire


def _game():
    return route_empire.new_game(location="Mitcham", players=["Alpha", "Bravo"])

def test_route_empire_creates_bounded_local_board():
    state = _game()
    view = route_empire.public_state(state)
    assert view["started"] is True
    assert view["location_label"] == "Mitcham"
    assert view["board_source"] == "synthetic_local_v1"
    assert view["precise_location_used"] is False
    assert len(view["nodes"]) == 8
    assert view["payments"] is False
    assert route_empire.validate(state)["passed"] is True

def test_claim_develop_route_and_turn_are_server_authoritative():
    state = _game()
    p1 = state["players"][0]["id"]
    state = route_empire.action(state, action="claim", node_id="north", request_id="claim0001")
    assert next(n for n in state["nodes"] if n["id"] == "north")["owner_id"] == p1
    state = route_empire.action(state, action="claim", node_id="market", request_id="claim0002")
    state = route_empire.action(state, action="route", node_id="north", target_node_id="market", request_id="route0001")
    state = route_empire.action(state, action="develop", node_id="north", request_id="develop01")
    assert state["players"][0]["influence"] == 6
    state = route_empire.action(state, action="end_turn", request_id="endturn01")
    assert state["turn_index"] == 1
    assert route_empire.validate(state)["passed"] is True

def test_duplicate_request_is_idempotent():
    state = _game()
    once = route_empire.action(state, action="claim", node_id="north", request_id="claim0001")
    twice = route_empire.action(once, action="claim", node_id="north", request_id="claim0001")
    assert twice == once

def test_fail_closed_boundaries():
    state = _game()
    state["nodes"][0]["owner_id"] = "tampered"
    try:
        route_empire.action(state, action="end_turn", request_id="endturn01")
        assert False
    except ValueError as exc:
        assert str(exc) == "route_empire_checkpoint_invalid"
