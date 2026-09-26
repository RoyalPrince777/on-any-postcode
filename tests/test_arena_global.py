from __future__ import annotations

import copy
import uuid

import pytest

from mission_control import arena_global


def _players(count=4):
    return [str(uuid.uuid4()) for _ in range(count)]


def test_league_records_results_and_projects_spectator_standings():
    players = _players()
    state = arena_global.create_league(name="CR4 League", level="POSTCODE", participant_ids=players)
    state = arena_global.record_result(
        state,
        player_a_id=players[0],
        player_b_id=players[1],
        player_a_score=7,
        player_b_score=3,
        receipt_hash="a" * 64,
    )
    view = arena_global.spectator_view(state)
    assert view["standings"][0]["participant_id"] == players[0]
    assert view["standings"][0]["points"] == 3
    assert view["payments"] is False
    assert view["prizes"] is False


def test_dispute_holds_progression_until_resolved():
    players = _players()
    state = arena_global.create_league(name="CR4 League", level="POSTCODE", participant_ids=players)
    state = arena_global.record_result(
        state, player_a_id=players[0], player_b_id=players[1],
        player_a_score=7, player_b_score=5, receipt_hash="b" * 64
    )
    result_id = state["results"][0]["result_id"]
    state = arena_global.open_dispute(
        state, result_id=result_id, raised_by=players[1], reason="Result evidence challenged"
    )
    assert state["status"] == "HELD"
    with pytest.raises(ValueError, match="arena_qualification_held"):
        arena_global.qualify_next_level(state)

    dispute_id = state["disputes"][0]["dispute_id"]
    state = arena_global.resolve_dispute(
        state, dispute_id=dispute_id, outcome="REJECTED", resolution="Receipt verified"
    )
    assert state["status"] == "ACTIVE"
    state = arena_global.qualify_next_level(state)
    assert state["status"] == "COMPLETED"
    assert state["next_level"] == "BOROUGH_REGION"


def test_progression_reaches_global_without_money_layer():
    players = _players(2)
    level = "POSTCODE"
    for expected_next in ("BOROUGH_REGION", "COUNTRY", "CONTINENT", "GLOBAL"):
        state = arena_global.create_league(name=f"{level} league", level=level, participant_ids=players)
        state = arena_global.record_result(
            state, player_a_id=players[0], player_b_id=players[1],
            player_a_score=7, player_b_score=0, receipt_hash=(expected_next[0].lower() if expected_next[0].lower() in "abcdef" else "f") * 64
        )
        state = arena_global.qualify_next_level(state)
        assert state["next_level"] == expected_next
        assert state["payments"] is False
        level = expected_next

    global_state = arena_global.create_league(name="Global Arena", level="GLOBAL", participant_ids=players)
    with pytest.raises(ValueError, match="arena_already_global"):
        arena_global.qualify_next_level(global_state)


def test_result_receipt_replay_idempotent_conflict_rejected():
    players = _players(2)
    state = arena_global.create_league(name="League", level="COUNTRY", participant_ids=players)
    state = arena_global.record_result(
        state, player_a_id=players[0], player_b_id=players[1],
        player_a_score=4, player_b_score=4, receipt_hash="c" * 64
    )
    replay = arena_global.record_result(
        state, player_a_id=players[0], player_b_id=players[1],
        player_a_score=4, player_b_score=4, receipt_hash="c" * 64
    )
    assert replay == state
    with pytest.raises(ValueError, match="arena_result_receipt_conflict"):
        arena_global.record_result(
            state, player_a_id=players[0], player_b_id=players[1],
            player_a_score=5, player_b_score=4, receipt_hash="c" * 64
        )


def test_divisions_and_stop_are_fail_closed():
    players = _players(2)
    state = arena_global.create_league(name="League", level="COUNTRY", participant_ids=players)
    state = arena_global.set_division(state, division="GOLD")
    assert state["division"] == "GOLD"
    state = arena_global.stop(state, reason="Safeguarding hold")
    assert state["status"] == "STOPPED"
    with pytest.raises(ValueError, match="arena_division_change_denied"):
        arena_global.set_division(state, division="ELITE")


def test_checkpoint_and_boundary_tamper_are_rejected():
    state = arena_global.create_league(name="League", level="CONTINENT", participant_ids=_players(2))
    tampered = copy.deepcopy(state)
    tampered["payments"] = True
    tampered["checkpoint"] = arena_global._digest({k: v for k, v in tampered.items() if k != "checkpoint"})
    check = arena_global.validate(tampered)
    assert check["passed"] is False
    assert "arena_global_boundary_invalid" in check["errors"]


def test_status_declares_only_proven_non_financial_capabilities():
    status = arena_global.status()
    assert status["leagues"] is True
    assert status["geographic_progression"] is True
    assert status["spectator_projection"] is True
    assert status["disputes"] is True
    assert status["payments"] is False
    assert status["prizes"] is False
    assert status["deployed"] is False


def test_non_integer_score_type_fails_with_type_error():
    players = _players(2)
    state = arena_global.create_league(name="League", level="COUNTRY", participant_ids=players)
    with pytest.raises(TypeError, match="arena_score_invalid"):
        arena_global.record_result(
            state,
            player_a_id=players[0],
            player_b_id=players[1],
            player_a_score="7",
            player_b_score=0,
            receipt_hash="d" * 64,
        )
