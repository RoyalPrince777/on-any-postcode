from mission_control import all_in_ai_action_bridge

IDENTITY = "00000000-0000-0000-0000-000000000001"
MISSION = "00000000-0000-0000-0000-000000000002"
REQUEST = "00000000-0000-0000-0000-000000000003"


def _mission_receipt(state="planned"):
    return {
        "state": state,
        "read_back_verified": True,
        "audit_verified": True,
        "hrm_verified": True,
    }


def _review(decision=None, *, guardian=True, judgement=True):
    return {
        "request_id": REQUEST,
        "output_state": "REVIEW_REQUIRED",
        "guardian_outcome": "PASSED" if guardian else "BLOCKED",
        "guardian_passed": guardian,
        "judgement_sections_completed": 5 if judgement else 4,
        "judgement_consistent": judgement,
        "human_decision": decision,
    }


def test_pending_human_authority_never_authorizes(monkeypatch):
    monkeypatch.setattr(
        all_in_ai_action_bridge.all_in_ai_mission_store,
        "read",
        lambda *_args, **_kwargs: _mission_receipt(),
    )
    monkeypatch.setattr(
        all_in_ai_action_bridge,
        "_review_status",
        lambda *_args, **_kwargs: _review(),
    )

    result = all_in_ai_action_bridge.handoff_status(
        IDENTITY,
        MISSION,
        reviewed_request_id=REQUEST,
    )

    assert result["status"] == "HUMAN_AUTHORITY_REQUIRED"
    assert result["execution_authorized"] is False
    assert result["execution_performed"] is False
    assert result["human_authority_final"] is True


def test_stopped_mission_fails_closed(monkeypatch):
    monkeypatch.setattr(
        all_in_ai_action_bridge.all_in_ai_mission_store,
        "read",
        lambda *_args, **_kwargs: _mission_receipt("stopped"),
    )

    try:
        all_in_ai_action_bridge.handoff_status(
            IDENTITY,
            MISSION,
            reviewed_request_id=REQUEST,
        )
    except all_in_ai_action_bridge.ActionHandoffBlocked as exc:
        assert str(exc) == "mission_stopped"
    else:
        raise AssertionError("STOPped mission must not advance")


def test_guardian_or_judgement_failure_blocks(monkeypatch):
    monkeypatch.setattr(
        all_in_ai_action_bridge.all_in_ai_mission_store,
        "read",
        lambda *_args, **_kwargs: _mission_receipt(),
    )
    monkeypatch.setattr(
        all_in_ai_action_bridge,
        "_review_status",
        lambda *_args, **_kwargs: _review(guardian=False),
    )
    guardian = all_in_ai_action_bridge.handoff_status(
        IDENTITY,
        MISSION,
        reviewed_request_id=REQUEST,
    )
    assert guardian["reason"] == "guardian_gate_required"
    assert guardian["execution_authorized"] is False

    monkeypatch.setattr(
        all_in_ai_action_bridge,
        "_review_status",
        lambda *_args, **_kwargs: _review(judgement=False),
    )
    judgement = all_in_ai_action_bridge.handoff_status(
        IDENTITY,
        MISSION,
        reviewed_request_id=REQUEST,
    )
    assert judgement["reason"] == "judgement_gate_required"
    assert judgement["execution_authorized"] is False


def test_signed_approval_can_authorize_but_bridge_never_executes(monkeypatch):
    monkeypatch.setattr(
        all_in_ai_action_bridge.all_in_ai_mission_store,
        "read",
        lambda *_args, **_kwargs: _mission_receipt(),
    )
    monkeypatch.setattr(
        all_in_ai_action_bridge,
        "_review_status",
        lambda *_args, **_kwargs: _review("APPROVED"),
    )
    monkeypatch.setattr(
        all_in_ai_action_bridge.governed_action_pipeline,
        "authorize_action",
        lambda **_kwargs: {
            "execution_authorized": True,
            "execution_performed": False,
            "human_authority_final": True,
        },
    )

    result = all_in_ai_action_bridge.handoff_status(
        IDENTITY,
        MISSION,
        reviewed_request_id=REQUEST,
    )

    assert result["status"] == "AUTHORIZED_NOT_EXECUTED"
    assert result["execution_authorized"] is True
    assert result["execution_performed"] is False
    assert result["authority_transferred"] is False


def test_bridge_status_creates_no_execution_authority():
    state = all_in_ai_action_bridge.status()
    assert state["execution_authority_created"] is False
    assert state["execution_performed_by_bridge"] is False
    assert state["signed_human_approval_required"] is True
    assert state["human_authority_final"] is True
