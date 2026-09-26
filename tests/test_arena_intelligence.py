from __future__ import annotations

import copy

import pytest

from mission_control import arena_intelligence, products


def test_arena_catalog_is_seven_layer_and_fail_closed():
    validation = arena_intelligence.validate_catalog()

    assert validation == {
        "passed": True,
        "errors": [],
        "checks": {
            "questions": 7,
            "intelligence_layers": 7,
            "progression_levels": 5,
            "live_a7_feeds": 0,
            "external_execution_edges": 0,
        },
    }
    assert all(value is False for value in arena_intelligence.PUBLIC_BOUNDARY.values())
    assert arena_intelligence.status() == {
        "id": "oap-arena",
        "name": "OAP Arena",
        "organ_id": "arena",
        "ready": True,
        "mode": "playable_session_scoped_non_ranked_challenge",
        "server_authoritative_rules": True,
        "idempotent_answers": True,
        "stop_enabled": True,
        "pause_resume_enabled": True,
        "audit_receipts": True,
        "checkpoint_recovery": True,
        "durable_persistence": False,
        "ranked_results": False,
        "multiplayer": False,
        "live_a7_feeds": False,
        "external_execution": False,
        "payments": False,
        "human_authority_final": True,
        "no_fake_green": True,
    }

    unsafe_boundary = {**arena_intelligence.PUBLIC_BOUNDARY, "payments": True}
    assert arena_intelligence.validate_catalog(boundary=unsafe_boundary)["passed"] is False


def test_server_authoritative_answer_is_idempotent_and_receipted():
    state = arena_intelligence.new_session()
    question = arena_intelligence.public_state(state)["question"]

    updated, result = arena_intelligence.answer(
        state,
        question_id=question["id"],
        choice_id="a",
        request_id="answer-request-0001",
    )
    duplicate_state, duplicate = arena_intelligence.answer(
        updated,
        question_id=question["id"],
        choice_id="a",
        request_id="answer-request-0001",
    )

    assert result["answered"] == 1
    assert result["score"] == 1
    assert result["feedback"]["correct"] is True
    assert duplicate["duplicate"] is True
    assert duplicate["answered"] == 1
    assert duplicate["score"] == 1
    assert duplicate_state == updated
    assert arena_intelligence.verify_receipt_chain(updated) is True
    assert arena_intelligence.validate_session(updated)["passed"] is True


def test_pause_resume_stop_and_tamper_recovery_boundary():
    state = arena_intelligence.new_session()
    paused, paused_view = arena_intelligence.transition(
        state, action="pause", request_id="pause-request-0001"
    )
    assert paused_view["status"] == "paused"
    with pytest.raises(ValueError, match="arena_session_paused"):
        question = arena_intelligence.public_state(paused)["question"]
        arena_intelligence.answer(
            paused,
            question_id=question["id"] if question else "arena-progression",
            choice_id="a",
            request_id="answer-request-0002",
        )

    resumed, resumed_view = arena_intelligence.transition(
        paused, action="resume", request_id="resume-request-0001"
    )
    assert resumed_view["status"] == "active"
    stopped, stopped_view = arena_intelligence.transition(
        resumed, action="stop", request_id="stop-request-0001"
    )
    assert stopped_view["status"] == "stopped"
    with pytest.raises(ValueError, match="arena_transition_denied"):
        arena_intelligence.transition(
            stopped, action="resume", request_id="resume-request-0002"
        )

    tampered = copy.deepcopy(stopped)
    tampered["score"] = 7
    validation = arena_intelligence.validate_session(tampered)
    assert validation["passed"] is False
    assert "arena_checkpoint_invalid" in validation["errors"]
    with pytest.raises(ValueError, match="arena_checkpoint_invalid"):
        arena_intelligence.transition(
            tampered, action="resume", request_id="resume-request-0003"
        )


def test_arena_public_routes_and_controls_are_real(anonymous_client):
    for path in ("/arena", "/world/arena", "/the-spot/arena"):
        response = anonymous_client.get(path)
        page = response.get_data(as_text=True)

        assert response.status_code == 200
        assert response.headers["Cache-Control"] == "no-store"
        assert "OAP <span class=\"arena-gold\">ARENA</span>" in page
        assert "OAP Challenge Engine" in page
        assert "One Combined Global Arena" in page
        assert "session-scoped, non-ranked Challenge Engine" in page
        assert "arena_intelligence.js" in page
        assert 'data-endpoint="/arena/session/start"' in page
        assert 'data-endpoint="/arena/session/stop"' in page

    capability = products.get_public_spot_capability("arena")
    assert capability == {
        "slug": "arena",
        "name": "OAP Arena",
        "purpose": "Play first-party challenges and progress from postcode to the Global Arena.",
    }


def test_arena_http_flow_requires_csrf_and_fails_closed(client, csrf):
    assert client.post("/arena/session/start", json={}).status_code == 403

    started = client.post(
        "/arena/session/start", json={}, headers={"X-OAP-CSRF": csrf["csrf_token"]}
    )
    assert started.status_code == 201
    start_body = started.get_json()
    assert start_body["status"] == "active"
    assert start_body["ranked"] is False
    assert start_body["durable"] is False

    question = start_body["question"]
    answered = client.post(
        "/arena/session/answer",
        json={
            "question_id": question["id"],
            "choice_id": "a",
            "request_id": "http-answer-0001",
        },
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )
    assert answered.status_code == 200
    assert answered.get_json()["answered"] == 1

    duplicate = client.post(
        "/arena/session/answer",
        json={
            "question_id": question["id"],
            "choice_id": "a",
            "request_id": "http-answer-0001",
        },
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )
    assert duplicate.status_code == 200
    assert duplicate.get_json()["duplicate"] is True
    assert duplicate.get_json()["answered"] == 1

    paused = client.post(
        "/arena/session/pause",
        json={"request_id": "http-pause-0001"},
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )
    assert paused.get_json()["status"] == "paused"
    denied = client.post(
        "/arena/session/answer",
        json={
            "question_id": answered.get_json()["question"]["id"],
            "choice_id": "a",
            "request_id": "http-answer-0002",
        },
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )
    assert denied.status_code == 409
    assert denied.get_json()["error"]["code"] == "arena_session_paused"

    resumed = client.post(
        "/arena/session/resume",
        json={"request_id": "http-resume-0001"},
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )
    assert resumed.get_json()["status"] == "active"
    stopped = client.post(
        "/arena/session/stop",
        json={"request_id": "http-stop-0001"},
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )
    assert stopped.get_json()["status"] == "stopped"
    assert stopped.get_json()["question"] is None

    recovered = client.post(
        "/arena/session/recover",
        json={},
        headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )
    assert recovered.status_code == 201
    assert recovered.get_json()["recovered"] is True
    assert recovered.get_json()["status"] == "active"


def test_public_script_has_no_tracking_or_client_side_score_authority(anonymous_client):
    script = anonymous_client.get("/static/arena_intelligence.js").get_data(as_text=True)

    assert 'post("/arena/session/answer"' in script
    assert "navigator.geolocation" not in script
    assert "localStorage" not in script
    assert "sessionStorage" not in script
    assert "correct_choice_id" not in script
    assert "state.score +=" not in script


def test_complete_challenge_fits_signed_session_and_does_not_publish(client, csrf):
    headers = {"X-OAP-CSRF": csrf["csrf_token"]}
    response = client.post("/arena/session/start", json={}, headers=headers)

    for index, question in enumerate(arena_intelligence.CHALLENGE_CATALOG, start=1):
        response = client.post(
            "/arena/session/answer",
            json={
                "question_id": question["id"],
                "choice_id": question["correct_choice_id"],
                "request_id": f"complete-answer-{index:04d}",
            },
            headers=headers,
        )
        assert response.status_code == 200

    result = response.get_json()
    assert result["status"] == "completed"
    assert result["score"] == 7
    assert result["ranked"] is False
    assert result["durable"] is False
    assert result["question"] is None
    assert result["receipt_count"] == 8
    assert len(response.headers.get("Set-Cookie", "")) < 4093
