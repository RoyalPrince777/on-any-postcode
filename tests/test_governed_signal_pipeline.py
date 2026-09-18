from __future__ import annotations

from mission_control import governed_signal_pipeline


def _brain(*, passed: bool = True):
    return {
        "passed": passed,
        "high_impact": True,
        "output_state": "REVIEW_REQUIRED",
        "advisor_ids": ["neo", "trinity"],
        "agent_count": 2,
        "analysis_summary": "Bounded governed recommendation.",
        "analysis_confidence": 0.91,
        "guardian_reason": "Safe for Human Authority review." if passed else "Guardian blocked.",
        "human_authority_final": True,
        "can_execute": False,
        "operational_coherence": {"coherent": True},
        "war_room": {
            "scenarios": ["Proceed", "Delay", "Reject"],
        },
    }


def test_action_fails_closed_without_human_authority(monkeypatch):
    monkeypatch.setattr(
        governed_signal_pipeline.live_brain,
        "review",
        lambda **_kwargs: _brain(),
    )
    called = []

    result = governed_signal_pipeline.run(
        request_id="request-1",
        identity_id="human-1",
        content="Deploy the reviewed change",
        requested_action="deploy",
        action_executor=lambda payload: called.append(payload) or {"executed": True},
    )

    assert result["human_authority"] == {
        "required": True,
        "approved": False,
        "final": True,
    }
    assert result["action"]["authorized"] is False
    assert result["action"]["executed"] is False
    assert result["action"]["state"] == "LOCKED"
    assert called == []
    assert result["hrm"]["receipt_built"] is False
    assert result["authority_transferred"] is False


def test_approved_action_uses_adapter_then_builds_hrm_receipt(monkeypatch):
    monkeypatch.setattr(
        governed_signal_pipeline.live_brain,
        "review",
        lambda **_kwargs: _brain(),
    )
    executed = []
    written = []

    def execute(payload):
        executed.append(payload)
        return {"executed": True, "proof": "adapter-proof"}

    def write(receipt):
        written.append(receipt)
        return {
            "receipt_id": receipt.receipt_id,
            "checksum": receipt.checksum,
            "write_verified": True,
            "read_back_verified": True,
        }

    result = governed_signal_pipeline.run(
        request_id="request-2",
        identity_id="founder-1",
        content="Deploy the reviewed change",
        requested_action="deploy",
        consequential=True,
        human_authority_approved=True,
        action_executor=execute,
        receipt_writer=write,
    )

    assert result["guardian"]["passed"] is True
    assert result["action"]["authorized"] is True
    assert result["action"]["executed"] is True
    assert result["action"]["state"] == "EXECUTED"
    assert len(executed) == 1
    assert executed[0]["human_authority_approved"] is True
    assert executed[0]["authority_transferred"] is False
    assert result["hrm"]["receipt_built"] is True
    assert result["hrm"]["durable_write_attempted"] is True
    assert len(written) == 1
    assert result["authority_transferred"] is False
    assert result["human_authority_final"] is True


def test_guardian_block_prevents_action_even_with_human_approval(monkeypatch):
    monkeypatch.setattr(
        governed_signal_pipeline.live_brain,
        "review",
        lambda **_kwargs: _brain(passed=False),
    )
    called = []

    result = governed_signal_pipeline.run(
        request_id="request-3",
        identity_id="founder-1",
        content="Execute a blocked action",
        requested_action="execute",
        human_authority_approved=True,
        action_executor=lambda payload: called.append(payload) or {"executed": True},
    )

    assert result["guardian"]["passed"] is False
    assert result["action"]["authorized"] is False
    assert result["action"]["executed"] is False
    assert called == []
    assert result["authority_transferred"] is False


def test_review_only_pipeline_never_executes(monkeypatch):
    monkeypatch.setattr(
        governed_signal_pipeline.live_brain,
        "review",
        lambda **_kwargs: _brain(),
    )

    result = governed_signal_pipeline.run(
        request_id="request-4",
        identity_id="human-1",
        content="Review system health",
        requested_action="review",
    )

    assert result["action"]["requested"] is False
    assert result["action"]["state"] == "REVIEW_ONLY"
    assert result["external_action_taken"] is False
    assert result["protocol"]["governance"] == "7-7-7"
    assert result["protocol"]["governed_checks"] == 21
