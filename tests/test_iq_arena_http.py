from mission_control import iq_arena


def test_iq_arena_http_flow(client, csrf):
    page = client.get("/arena/iq")
    assert page.status_code == 200
    body = page.get_data(as_text=True)
    assert "IQ Arena" in body
    assert "Think. Solve. Adapt." in body
    assert "not a clinical or standardized IQ test" in body
    assert "iq_arena.js" in body

    assert client.post("/arena/iq/start", json={}).status_code == 403
    headers = {"X-OAP-CSRF": csrf["csrf_token"]}
    started = client.post("/arena/iq/start", json={}, headers=headers)
    assert started.status_code == 201
    state = started.get_json()
    assert state["status"] == "active"
    assert state["clinical_iq_score"] is False
    assert state["skill_profile_only"] is True

    question = state["question"]
    source = next(item for item in iq_arena.QUESTIONS if item["id"] == question["id"])
    answered = client.post(
        "/arena/iq/answer",
        json={
            "question_id": question["id"],
            "choice_id": source["answer"],
            "request_id": "http-iq-answer-0001",
        },
        headers=headers,
    )
    assert answered.status_code == 200
    assert answered.get_json()["score"] == 1

    stopped = client.post(
        "/arena/iq/stop",
        json={"request_id": "http-iq-stop-0001"},
        headers=headers,
    )
    assert stopped.status_code == 200
    assert stopped.get_json()["status"] == "stopped"
