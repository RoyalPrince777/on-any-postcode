import pytest

from mission_control import ludo


def reseal(state):
    return ludo._seal(state)


def test_ludo_starts_with_four_tokens_in_each_yard():
    state = ludo.new_game(["Alpha", "Bravo"])
    view = ludo.public_state(state)
    assert [player["pieces"] for player in view["players"]] == [[-1] * 4, [-1] * 4]
    assert view["die"] is None
    assert view["legal_pieces"] == []
    assert view["ruleset"] == "Ludo classic core"


def test_six_is_required_to_leave_yard_and_grants_bonus_turn():
    state = ludo.new_game(["Alpha", "Bravo"])
    state = ludo.roll(state, request_id="ludo-roll-0001", forced_die=6)
    assert ludo.public_state(state)["legal_pieces"] == [0, 1, 2, 3]
    state = ludo.move(state, piece_index=0, request_id="ludo-move-0001")
    assert state["players"][0]["pieces"][0] == 0
    assert state["turn_index"] == 0
    assert state["die"] is None


def test_non_six_with_all_tokens_in_yard_passes_turn():
    state = ludo.new_game(["Alpha", "Bravo"])
    state = ludo.roll(state, request_id="ludo-roll-0002", forced_die=3)
    assert state["turn_index"] == 1
    assert state["die"] is None
    assert state["request_receipts"][-1]["passed"] is True


def test_capture_sends_opponent_back_to_yard_and_grants_bonus_turn():
    state = ludo.new_game(["Alpha", "Bravo"])
    state["players"][0]["pieces"][0] = 5
    state["players"][1]["pieces"][0] = 45  # Bravo global square 6.
    state["turn_index"] = 0
    state["die"] = 1
    state = reseal(state)

    state = ludo.move(state, piece_index=0, request_id="ludo-move-0002")
    assert state["players"][0]["pieces"][0] == 6
    assert state["players"][1]["pieces"][0] == -1
    assert state["turn_index"] == 0
    assert state["request_receipts"][-1]["captured"] == [
        {"player_id": "p2", "piece_index": 0}
    ]


def test_safe_square_prevents_capture():
    state = ludo.new_game(["Alpha", "Bravo"])
    state["players"][0]["pieces"][0] = 7
    state["players"][1]["pieces"][0] = 47  # Bravo global square 8.
    state["turn_index"] = 0
    state["die"] = 1
    state = reseal(state)

    state = ludo.move(state, piece_index=0, request_id="ludo-move-0003")
    assert state["players"][0]["pieces"][0] == 8
    assert state["players"][1]["pieces"][0] == 47
    assert state["request_receipts"][-1]["captured"] == []


def test_exact_roll_is_required_to_finish():
    state = ludo.new_game(["Alpha", "Bravo"])
    state["players"][0]["pieces"][0] = ludo.FINISH - 2
    state["turn_index"] = 0
    state["die"] = 3
    state = reseal(state)
    assert ludo.public_state(state)["legal_pieces"] == []

    state["die"] = 2
    state = reseal(state)
    state = ludo.move(state, piece_index=0, request_id="ludo-move-0004")
    assert state["players"][0]["pieces"][0] == ludo.FINISH


def test_all_four_tokens_must_finish_to_win():
    state = ludo.new_game(["Alpha", "Bravo"])
    state["players"][0]["pieces"] = [ludo.FINISH, ludo.FINISH, ludo.FINISH, ludo.FINISH - 1]
    state["turn_index"] = 0
    state["die"] = 1
    state = reseal(state)

    state = ludo.move(state, piece_index=3, request_id="ludo-move-0005")
    assert state["status"] == "completed"
    assert state["winner_id"] == "p1"


def test_three_consecutive_sixes_forfeit_third_roll():
    state = ludo.new_game(["Alpha", "Bravo"])
    state = ludo.roll(state, request_id="ludo-roll-0003", forced_die=6)
    state = ludo.move(state, piece_index=0, request_id="ludo-move-0006")
    state = ludo.roll(state, request_id="ludo-roll-0004", forced_die=6)
    state = ludo.move(state, piece_index=0, request_id="ludo-move-0007")
    state = ludo.roll(state, request_id="ludo-roll-0005", forced_die=6)
    assert state["turn_index"] == 1
    assert state["die"] is None
    assert state["request_receipts"][-1]["forfeited"] is True


def test_roll_and_stop_retries_are_idempotent():
    state = ludo.new_game(["Alpha", "Bravo"])
    rolled = ludo.roll(state, request_id="ludo-roll-0006", forced_die=6)
    assert ludo.roll(rolled, request_id="ludo-roll-0006", forced_die=1) == rolled

    stopped = ludo.stop(rolled, request_id="ludo-stop-0001")
    assert ludo.stop(stopped, request_id="ludo-stop-0001") == stopped
    with pytest.raises(ValueError, match="ludo_stop_denied"):
        ludo.stop(stopped, request_id="ludo-stop-0002")
