import copy

import pytest

from mission_control import ludo
from mission_control.arena_ludo_shere_khan import (
    LEVEL_NAMES,
    choose_shere_khan_piece,
)


def test_levels_are_named_and_selection_never_mutates_state():
    state = ludo.new_game(["Human", "Shere Khan"])
    state = ludo.roll(state, request_id="ludo-agent-roll-0001", die_value=6)
    original = copy.deepcopy(state)
    for level in LEVEL_NAMES:
        picked = choose_shere_khan_piece(state, level)
        assert picked in ludo._movable_piece_ids(state, 6)
    assert state == original


def test_all_levels_refuse_unrolled_state():
    state = ludo.new_game(["Human", "Shere Khan"])
    for level in LEVEL_NAMES:
        with pytest.raises(ValueError, match="ludo_agent_roll_required"):
            choose_shere_khan_piece(state, level)


def test_advanced_tier_selects_capture_without_modifying_engine_rules():
    state = ludo.new_game(["Human", "Shere Khan"])
    human, khan = state["players"]
    human["pieces"][0]["progress"] = 2
    # Khan progress 39 maps to square 13+39=52 (0), so rolling 2 reaches square 2.
    khan["pieces"][0]["progress"] = 39
    khan["pieces"][1]["progress"] = 1
    state["turn_index"] = 1
    state["pending_roll"] = 2
    state = ludo._seal(state)
    assert choose_shere_khan_piece(state, "tyrant") == khan["pieces"][0]["id"]


def test_invalid_level_and_no_legal_piece_fail_closed():
    state = ludo.new_game(["Human", "Shere Khan"])
    with pytest.raises(ValueError, match="ludo_agent_level_invalid"):
        choose_shere_khan_piece(state, "unknown")
    state = ludo.roll(state, request_id="ludo-agent-roll-0002", die_value=5)
    # With no pieces deployed and a non-six, the engine advances instead of
    # storing pending_roll: policy must never fabricate an AI move.
    with pytest.raises(ValueError, match="ludo_agent_roll_required"):
        choose_shere_khan_piece(state, "cub")
