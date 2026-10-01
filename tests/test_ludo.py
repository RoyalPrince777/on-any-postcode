import pytest

from mission_control import ludo


def _roll(state, value, request_id):
    return ludo.roll(state, die_value=value, request_id=request_id)


def test_ludo_starts_with_four_pieces_each_in_yard():
    state = ludo.new_game(["Alpha", "Bravo"])
    assert len(state["players"]) == 2
    assert all(len(player["pieces"]) == 4 for player in state["players"])
    assert all(
        piece["progress"] == -1
        for player in state["players"]
        for piece in player["pieces"]
    )


def test_ludo_requires_six_to_enter_and_six_keeps_turn():
    state = ludo.new_game(["Alpha", "Bravo"])
    state = _roll(state, 5, "ludo-roll-0001")
    assert state["pending_roll"] is None
    assert state["turn_index"] == 1

    state = _roll(state, 6, "ludo-roll-0002")
    assert state["pending_roll"] == 6
    state = ludo.move(state, piece_id="p2-1", request_id="ludo-move-0002")
    assert state["players"][1]["pieces"][0]["progress"] == 0
    assert state["turn_index"] == 1


def test_ludo_moves_selected_piece_and_requires_exact_finish():
    state = ludo.new_game(["Alpha", "Bravo"])
    state["players"][0]["pieces"][0]["progress"] = ludo.FINISH_PROGRESS - 2
    state["players"][0]["pieces"][1]["progress"] = 0
    state = ludo._seal(state)

    state = _roll(state, 3, "ludo-roll-0003")
    with pytest.raises(ValueError, match="ludo_piece_move_invalid"):
        ludo.move(state, piece_id="p1-1", request_id="ludo-move-0003")

    state["pending_roll"] = None
    state = ludo._seal(state)
    state = _roll(state, 2, "ludo-roll-0004")
    state = ludo.move(state, piece_id="p1-1", request_id="ludo-move-0004")
    assert state["players"][0]["pieces"][0]["progress"] == ludo.FINISH_PROGRESS


def test_ludo_capture_returns_opponent_to_yard_and_grants_extra_turn():
    state = ludo.new_game(["Alpha", "Bravo"])
    state["players"][0]["pieces"][0]["progress"] = 1
    # Bravo start offset is 13, so progress 41 maps to shared square 2.
    state["players"][1]["pieces"][0]["progress"] = 41
    state = ludo._seal(state)

    state = _roll(state, 1, "ludo-roll-0005")
    state = ludo.move(state, piece_id="p1-1", request_id="ludo-move-0005")
    assert state["players"][0]["pieces"][0]["progress"] == 2
    assert state["players"][1]["pieces"][0]["progress"] == -1
    assert state["turn_index"] == 0
    assert state["request_receipts"][-1]["captured"] == ["p2-1"]


def test_ludo_safe_square_prevents_capture():
    state = ludo.new_game(["Alpha", "Bravo"])
    state["players"][0]["pieces"][0]["progress"] = 7
    # Alpha lands on shared safe square 8; Bravo's progress 47 also maps to 8.
    state["players"][1]["pieces"][0]["progress"] = 47
    state = ludo._seal(state)

    state = _roll(state, 1, "ludo-roll-0006")
    state = ludo.move(state, piece_id="p1-1", request_id="ludo-move-0006")
    assert state["players"][1]["pieces"][0]["progress"] == 47
    assert state["turn_index"] == 1


def test_ludo_all_four_finished_wins():
    state = ludo.new_game(["Alpha", "Bravo"])
    for piece in state["players"][0]["pieces"][:3]:
        piece["progress"] = ludo.FINISH_PROGRESS
    state["players"][0]["pieces"][3]["progress"] = ludo.FINISH_PROGRESS - 1
    state = ludo._seal(state)

    state = _roll(state, 1, "ludo-roll-0007")
    state = ludo.move(state, piece_id="p1-4", request_id="ludo-move-0007")
    assert state["status"] == "completed"
    assert state["winner_id"] == "p1"


def test_ludo_roll_and_move_are_idempotent():
    state = ludo.new_game(["Alpha", "Bravo"])
    rolled = _roll(state, 6, "ludo-roll-0008")
    assert ludo.roll(rolled, request_id="ludo-roll-0008") == rolled

    moved = ludo.move(rolled, piece_id="p1-1", request_id="ludo-move-0008")
    assert ludo.move(moved, piece_id="p1-1", request_id="ludo-move-0008") == moved
