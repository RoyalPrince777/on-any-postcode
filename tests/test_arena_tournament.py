from __future__ import annotations

import copy
import uuid

import pytest

from mission_control import arena_tournament


def _teams():
    return [
        arena_tournament.create_team(name=f"Team {n}", member_ids=[str(uuid.uuid4())])
        for n in range(1, 5)
    ]


def test_four_team_bracket_progresses_to_champion():
    teams = _teams()
    state = arena_tournament.create_tournament(name="Global Test Cup", teams=teams)
    assert arena_tournament.validate_tournament(state)["passed"] is True

    state = arena_tournament.record_result(
        state, match_no=1, winner_team_id=teams[0]["team_id"], receipt_hash="a" * 64
    )
    state = arena_tournament.record_result(
        state, match_no=2, winner_team_id=teams[2]["team_id"], receipt_hash="b" * 64
    )
    view = arena_tournament.public_state(state)
    assert view["matches"][2]["team_a_id"] == teams[0]["team_id"]
    assert view["matches"][2]["team_b_id"] == teams[2]["team_id"]

    state = arena_tournament.record_result(
        state, match_no=3, winner_team_id=teams[2]["team_id"], receipt_hash="c" * 64
    )
    view = arena_tournament.public_state(state)
    assert view["status"] == "COMPLETED"
    assert view["champion_team_id"] == teams[2]["team_id"]
    assert view["payments"] is False
    assert view["prizes"] is False


def test_result_requires_scheduled_participant_and_unique_receipt():
    teams = _teams()
    state = arena_tournament.create_tournament(name="Cup", teams=teams)

    with pytest.raises(ValueError, match="arena_tournament_winner_not_participant"):
        arena_tournament.record_result(
            state, match_no=1, winner_team_id=teams[3]["team_id"], receipt_hash="a" * 64
        )

    state = arena_tournament.record_result(
        state, match_no=1, winner_team_id=teams[0]["team_id"], receipt_hash="a" * 64
    )
    with pytest.raises(ValueError, match="arena_tournament_receipt_reused"):
        arena_tournament.record_result(
            state, match_no=2, winner_team_id=teams[2]["team_id"], receipt_hash="a" * 64
        )


def test_exact_result_replay_is_idempotent_and_conflict_fails_closed():
    teams = _teams()
    state = arena_tournament.create_tournament(name="Cup", teams=teams)
    state = arena_tournament.record_result(
        state, match_no=1, winner_team_id=teams[0]["team_id"], receipt_hash="a" * 64
    )

    replay = arena_tournament.record_result(
        state, match_no=1, winner_team_id=teams[0]["team_id"], receipt_hash="a" * 64
    )
    assert replay == state

    with pytest.raises(ValueError, match="arena_tournament_result_conflict"):
        arena_tournament.record_result(
            state, match_no=1, winner_team_id=teams[1]["team_id"], receipt_hash="b" * 64
        )


def test_final_cannot_be_recorded_before_semifinals():
    teams = _teams()
    state = arena_tournament.create_tournament(name="Cup", teams=teams)
    with pytest.raises(ValueError, match="arena_tournament_match_not_ready"):
        arena_tournament.record_result(
            state, match_no=3, winner_team_id=teams[0]["team_id"], receipt_hash="c" * 64
        )


def test_member_cannot_join_two_teams_in_same_tournament():
    shared = str(uuid.uuid4())
    teams = [
        arena_tournament.create_team(name="A", member_ids=[shared]),
        arena_tournament.create_team(name="B", member_ids=[shared]),
        arena_tournament.create_team(name="C", member_ids=[str(uuid.uuid4())]),
        arena_tournament.create_team(name="D", member_ids=[str(uuid.uuid4())]),
    ]
    with pytest.raises(ValueError, match="arena_tournament_member_on_multiple_teams"):
        arena_tournament.create_tournament(name="Cup", teams=teams)


def test_stop_is_terminal_and_checkpoint_tamper_fails():
    teams = _teams()
    state = arena_tournament.create_tournament(name="Cup", teams=teams)
    stopped = arena_tournament.stop_tournament(state, reason="Integrity review")
    assert arena_tournament.public_state(stopped)["status"] == "STOPPED"
    with pytest.raises(ValueError, match="arena_tournament_not_active"):
        arena_tournament.record_result(
            stopped, match_no=1, winner_team_id=teams[0]["team_id"], receipt_hash="d" * 64
        )

    tampered = copy.deepcopy(state)
    tampered["champion_team_id"] = teams[0]["team_id"]
    check = arena_tournament.validate_tournament(tampered)
    assert check["passed"] is False
    assert "arena_tournament_checkpoint_invalid" in check["errors"]


def test_money_boundary_is_fail_closed():
    teams = _teams()
    state = arena_tournament.create_tournament(name="Cup", teams=teams)
    tampered = copy.deepcopy(state)
    tampered["payments"] = True
    tampered["checkpoint"] = arena_tournament._digest(arena_tournament._unsealed(tampered))
    check = arena_tournament.validate_tournament(tampered)
    assert check["passed"] is False
    assert "arena_tournament_money_boundary_invalid" in check["errors"]
