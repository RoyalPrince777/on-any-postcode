"""Shared integrity regression for the three OAP Arena priority games.

This proves fresh game isolation and rejects in-memory tampering before any
room/deployment claims. It does NOT certify live multiplayer or Home Node.
"""
from __future__ import annotations

import copy

import pytest

from mission_control import chess, connect4, oware


@pytest.mark.parametrize(
    ("create", "mutate"),
    [
        (
            lambda: connect4.new_game("Alpha", "Bravo"),
            lambda state: state["board"][5].__setitem__(0, 1),
        ),
        (
            chess.new_game,
            lambda state: state["board"].__setitem__("e2", "wQ"),
        ),
        (
            oware.new_game,
            lambda state: state["pits"].__setitem__(0, 5),
        ),
    ],
    ids=["connect4", "chess", "oware-abapa"],
)
def test_priority_game_integrity_and_fresh_session_isolation(create, mutate):
    original = create()
    second = create()

    assert original["game_id"] != second["game_id"]
    assert original["status"] == "active"
    assert second["status"] == "active"

    pristine_second = copy.deepcopy(second)
    changed = copy.deepcopy(original)
    mutate(changed)

    # Every authoritative engine must reject an altered sealed state.
    check = (
        connect4.validate if "connect4" in original["schema"]
        else chess.validate if "chess" in original["schema"]
        else oware.validate
    )
    assert check(original)["passed"] is True
    assert check(changed)["passed"] is False
    assert second == pristine_second
    assert check(second)["passed"] is True


def test_oware_abapa_and_chess_opening_identity():
    seeds = oware.public_state(oware.new_game())
    assert len(seeds["pits"]) == 12
    assert sum(seeds["pits"]) == 48
    assert seeds["ruleset"] == "Abapa core"

    board = chess.public_state(chess.new_game())["board"]
    assert board["d1"] == "wQ"
    assert board["d8"] == "bQ"
    assert board["e1"] == "wK"
    assert board["e8"] == "bK"
