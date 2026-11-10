from __future__ import annotations

import pytest

from mission_control import iq_duel


def test_iq_duel_hides_score_until_both_answer_same_question():
    state = iq_duel.new_game(["Alpha", "Bravo"])
    first = iq_duel.public_state(state, seat=1)
    assert first["question"]["id"] == "logic-1"
    assert first["players"][0]["score"] == 0
    assert first["players"][1]["score"] == 0

    state = iq_duel.answer(
        state, seat=1, choice_id="b", request_id="iq-duel-alpha-0001"
    )
    after_one = iq_duel.public_state(state, seat=1)
    other_view = iq_duel.public_state(state, seat=2)
    assert after_one["your_answer_locked"] is True
    assert other_view["your_answer_locked"] is False
    assert after_one["players"][0]["score"] == 0
    assert after_one["question"]["id"] == "logic-1"

    state = iq_duel.answer(
        state, seat=2, choice_id="a", request_id="iq-duel-bravo-0001"
    )
    after_both = iq_duel.public_state(state, seat=1)
    assert after_both["players"][0]["score"] == 1
    assert after_both["players"][1]["score"] == 0
    assert after_both["question"]["id"] == "patterns-1"
    assert after_both["answered_seats"] == []


def test_iq_duel_rejects_double_answer_and_is_not_clinical():
    state = iq_duel.new_game(["Alpha", "Bravo"])
    state = iq_duel.answer(
        state, seat=1, choice_id="b", request_id="iq-duel-once-0001"
    )
    with pytest.raises(ValueError, match="iq_duel_answer_already_locked"):
        iq_duel.answer(
            state, seat=1, choice_id="a", request_id="iq-duel-twice-0001"
        )
    view = iq_duel.public_state(state, seat=1)
    assert view["skill_profile_only"] is True
    assert view["clinical_iq_score"] is False
    assert view["payments"] is False


def test_iq_duel_stop_is_terminal():
    state = iq_duel.new_game(["Alpha", "Bravo"])
    state = iq_duel.stop(state, request_id="iq-duel-stop-0001")
    assert iq_duel.public_state(state, seat=1)["status"] == "stopped"
    with pytest.raises(ValueError, match="iq_duel_not_active"):
        iq_duel.answer(
            state, seat=1, choice_id="b", request_id="iq-duel-after-stop-0001"
        )
