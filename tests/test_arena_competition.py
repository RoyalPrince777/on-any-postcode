from __future__ import annotations

import copy

import pytest

from mission_control import arena_competition, arena_intelligence


def _active_match():
    state = arena_competition.create_match(creator_id="player-alpha")
    state, _ = arena_competition.join_match(
        state,
        player_id="player-beta",
        request_id="join-request-0001",
    )
    return state


def test_match_creation_and_join_are_bounded_and_receipted():
    state = arena_competition.create_match(creator_id="player-alpha")
    public = arena_competition.public_match(state)

    assert public["status"] == "waiting"
    assert public["ranked"] is False
    assert public["durable"] is False
    assert public["payments"] is False
    assert public["prizes"] is False

    joined, joined_public = arena_competition.join_match(
        state,
        player_id="player-beta",
        request_id="join-request-0001",
    )

    assert joined_public["status"] == "active"
    assert [item["player_id"] for item in joined_public["players"]] == [
        "player-alpha",
        "player-beta",
    ]
    assert arena_competition.verify_receipt_chain(joined) is True
    assert arena_competition.validate_match(joined)["passed"] is True


def test_duplicate_join_request_is_idempotent_but_duplicate_player_is_rejected():
    state = arena_competition.create_match(creator_id="player-alpha")
    joined, _ = arena_competition.join_match(
        state,
        player_id="player-beta",
        request_id="join-request-0001",
    )
    duplicate_state, duplicate = arena_competition.join_match(
        joined,
        player_id="player-beta",
        request_id="join-request-0001",
    )

    assert duplicate["duplicate"] is True
    assert duplicate_state == joined

    fresh = arena_competition.create_match(creator_id="player-alpha")
    with pytest.raises(ValueError, match="arena_match_duplicate_player"):
        arena_competition.join_match(
            fresh,
            player_id="player-alpha",
            request_id="join-request-0002",
        )


def test_two_players_answer_before_server_closes_round():
    state = _active_match()
    question = arena_competition.public_match(state)["question"]

    after_alpha, alpha_view = arena_competition.submit_answer(
        state,
        player_id="player-alpha",
        question_id=question["id"],
        choice_id=arena_intelligence.CHALLENGE_CATALOG[0]["correct_choice_id"],
        request_id="answer-alpha-0001",
    )

    assert alpha_view["question_index"] == 0
    assert alpha_view["scores"] == {"player-alpha": 0, "player-beta": 0}
    assert alpha_view["answered_player_ids"] == ("player-alpha",)

    after_beta, beta_view = arena_competition.submit_answer(
        after_alpha,
        player_id="player-beta",
        question_id=question["id"],
        choice_id="b",
        request_id="answer-beta-0001",
    )

    assert beta_view["question_index"] == 1
    assert beta_view["scores"] == {"player-alpha": 1, "player-beta": 0}
    assert beta_view["answered_player_ids"] == ()
    assert arena_competition.validate_match(after_beta)["passed"] is True


def test_answer_replay_duplicate_answer_and_non_member_fail_closed():
    state = _active_match()
    question = arena_competition.public_match(state)["question"]

    answered, _ = arena_competition.submit_answer(
        state,
        player_id="player-alpha",
        question_id=question["id"],
        choice_id="a",
        request_id="answer-alpha-0001",
    )
    duplicate_state, duplicate = arena_competition.submit_answer(
        answered,
        player_id="player-alpha",
        question_id=question["id"],
        choice_id="a",
        request_id="answer-alpha-0001",
    )
    assert duplicate["duplicate"] is True
    assert duplicate_state == answered

    with pytest.raises(ValueError, match="arena_match_player_already_answered"):
        arena_competition.submit_answer(
            answered,
            player_id="player-alpha",
            question_id=question["id"],
            choice_id="a",
            request_id="answer-alpha-0002",
        )

    with pytest.raises(ValueError, match="arena_match_player_not_member"):
        arena_competition.submit_answer(
            answered,
            player_id="player-gamma",
            question_id=question["id"],
            choice_id="a",
            request_id="answer-gamma-0001",
        )


def test_forged_score_and_broken_receipt_chain_are_rejected():
    state = _active_match()

    forged = copy.deepcopy(state)
    forged["scores"]["player-alpha"] = 7
    validation = arena_competition.validate_match(forged)
    assert validation["passed"] is False
    assert "arena_match_checkpoint_invalid" in validation["errors"]

    broken = copy.deepcopy(state)
    broken["receipts"][0]["detail"]["creator_id"] = "attacker"
    broken["checkpoint"] = arena_competition._digest(arena_competition._unsealed(broken))
    validation = arena_competition.validate_match(broken)
    assert validation["passed"] is False
    assert "arena_match_receipt_chain_invalid" in validation["errors"]


def test_stop_is_terminal_and_member_scoped():
    state = _active_match()

    with pytest.raises(ValueError, match="arena_match_player_not_member"):
        arena_competition.stop_match(
            state,
            actor_id="player-gamma",
            request_id="stop-gamma-0001",
        )

    stopped, stopped_view = arena_competition.stop_match(
        state,
        actor_id="player-alpha",
        request_id="stop-alpha-0001",
    )

    assert stopped_view["status"] == "stopped"
    assert stopped_view["question"] is None

    with pytest.raises(ValueError, match="arena_match_stopped"):
        arena_competition.submit_answer(
            stopped,
            player_id="player-beta",
            question_id=arena_intelligence.CHALLENGE_CATALOG[0]["id"],
            choice_id="a",
            request_id="answer-beta-0002",
        )


def test_full_match_completes_with_server_authoritative_result():
    state = _active_match()

    for index, question in enumerate(arena_intelligence.CHALLENGE_CATALOG, start=1):
        state, _ = arena_competition.submit_answer(
            state,
            player_id="player-alpha",
            question_id=question["id"],
            choice_id=question["correct_choice_id"],
            request_id=f"full-alpha-{index:04d}",
        )
        state, view = arena_competition.submit_answer(
            state,
            player_id="player-beta",
            question_id=question["id"],
            choice_id=question["choices"][0]["id"],
            request_id=f"full-beta-{index:04d}",
        )

    assert view["status"] == "completed"
    assert view["question"] is None
    assert view["result"]["scores"] == view["scores"]
    assert view["result"]["winner_ids"]
    assert arena_competition.validate_match(state)["passed"] is True


def test_competition_status_does_not_claim_locked_layers():
    assert arena_competition.status() == {
        "id": "oap-arena-competition",
        "mode": "two_player_non_ranked_isolated_engine",
        "two_player_match_state": True,
        "server_authoritative_scoring": True,
        "idempotent_requests": True,
        "stop_enabled": True,
        "audit_receipts": True,
        "checkpoint_recovery": True,
        "durable_profiles": False,
        "rankings": False,
        "payments": False,
        "prizes": False,
        "public_routes": False,
        "deployed": False,
        "no_fake_green": True,
    }
