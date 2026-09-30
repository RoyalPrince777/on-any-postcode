"""Oware Abapa-core regression tests."""
import copy

import pytest

from mission_control import oware


def reseal(state):
    state = copy.deepcopy(state)
    state.pop("checkpoint", None)
    return oware._seal(state)


def test_new_game_has_twelve_houses_and_forty_eight_seeds():
    state = oware.new_game(["Ama", "Kojo"])
    public = oware.public_state(state)
    assert public["pits"] == [4] * 12
    assert sum(public["pits"]) == 48
    assert public["legal_pits"] == [0, 1, 2, 3, 4, 5]
    assert public["ruleset"] == "Abapa core"


def test_sowing_skips_origin_after_full_lap():
    state = oware.new_game()
    state["pits"] = [12, 0, 0, 0, 0, 0, 4, 4, 4, 4, 4, 4]
    state["players"][0]["captured"] = 12
    state = reseal(state)
    moved = oware.move(state, pit=0, request_id="oware-move-0001")
    assert moved["pits"][0] == 0
    assert moved["pits"][1] == 2


def test_capture_walks_backward_over_opponent_twos_and_threes():
    state = oware.new_game()
    state["pits"] = [0, 0, 0, 0, 0, 3, 1, 1, 4, 4, 4, 4]
    state["players"][0]["captured"] = 22
    state["players"][1]["captured"] = 5
    state = reseal(state)
    moved = oware.move(state, pit=5, request_id="oware-move-0002")
    assert moved["players"][0]["captured"] == 26
    assert moved["pits"][6] == 0
    assert moved["pits"][7] == 0
    assert moved["status"] == "completed"
    assert moved["winner_id"] == "p1"


def test_grand_slam_capture_is_forfeited_to_avoid_starvation():
    state = oware.new_game()
    state["pits"] = [0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0]
    state["players"][0]["captured"] = 23
    state["players"][1]["captured"] = 23
    state = reseal(state)
    moved = oware.move(state, pit=5, request_id="oware-move-0003")
    assert moved["players"][0]["captured"] == 23
    assert sum(moved["pits"][6:]) == 2
    assert moved["request_receipts"][-1]["grand_slam_forfeited"] is True


def test_empty_opponent_must_be_fed_when_possible():
    state = oware.new_game()
    state["pits"] = [1, 0, 0, 0, 0, 7, 0, 0, 0, 0, 0, 0]
    state["players"][0]["captured"] = 20
    state["players"][1]["captured"] = 20
    state = reseal(state)
    assert oware.legal_pits(state) == [5]
    with pytest.raises(ValueError, match="move_not_legal"):
        oware.move(state, pit=0, request_id="oware-move-0004")


def test_stop_retry_is_idempotent():
    state = oware.new_game()
    stopped = oware.stop(state, request_id="oware-stop-0001")
    assert oware.stop(stopped, request_id="oware-stop-0001") == stopped
    with pytest.raises(ValueError, match="stop_denied"):
        oware.stop(stopped, request_id="oware-stop-0002")
