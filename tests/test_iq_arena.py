from mission_control import iq_arena


def test_iq_arena_reports_skill_profile_not_clinical_iq():
    state = iq_arena.new_session()
    view = iq_arena.public_state(state)
    assert view["started"] is True
    assert view["skill_profile_only"] is True
    assert view["clinical_iq_score"] is False
    assert view["diagnostic_use"] is False
    assert set(view["domain_scores"]) == set(iq_arena.DOMAINS)


def test_iq_arena_scores_server_side_and_completes():
    state = iq_arena.new_session()
    for index, question in enumerate(iq_arena.QUESTIONS, start=1):
        state = iq_arena.answer(
            state,
            question_id=question["id"],
            choice_id=question["answer"],
            request_id=f"answer-{index:04d}",
        )
    view = iq_arena.public_state(state)
    assert view["status"] == "completed"
    assert view["score"] == 7
    assert all(value == 1 for value in view["domain_scores"].values())


def test_iq_arena_duplicate_request_is_idempotent_and_stop_fails_closed():
    state = iq_arena.new_session()
    question = iq_arena.QUESTIONS[0]
    once = iq_arena.answer(state, question_id=question["id"], choice_id=question["answer"], request_id="answer-0001")
    twice = iq_arena.answer(once, question_id="wrong", choice_id="z", request_id="answer-0001")
    assert twice == once
    stopped = iq_arena.stop(twice, request_id="stop-00001")
    assert stopped["status"] == "stopped"


def test_iq_arena_exposes_last_answer_feedback_and_accuracy():
    state = iq_arena.new_session()
    q = iq_arena.QUESTIONS[0]
    state = iq_arena.answer(
        state,
        question_id=q["id"],
        choice_id=q["answer"],
        request_id="answer-feedback-0001",
    )
    view = iq_arena.public_state(state)
    assert view["last_answer"] == {
        "question_id": q["id"],
        "domain": q["domain"],
        "correct": True,
    }
    assert view["accuracy_percent"] == 100
