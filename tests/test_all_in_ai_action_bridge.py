from mission_control import all_in_ai_action_bridge

IDENTITY = "00000000-0000-0000-0000-000000000001"
MISSION = "00000000-0000-0000-0000-000000000002"
REQUEST = "00000000-0000-0000-0000-000000000003"
MISSION_HASH = "a" * 64


def _mission_receipt(state="planned"):
    return {
        "mission_hash": MISSION_HASH,
        "state": state,
        "read_back_verified": True,
        "audit_verified": True,
        "hrm_verified": True,
    }


def _review(decision=None, *, guardian=True, judgement=True):
    return {
        "request_id": REQUEST,
        "output_state": "REVIEW_REQUIRED",
        "content_hash": MISSION_HASH,
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


def test_other_review_cannot_authorize_or_execute_this_mission(monkeypatch):
    monkeypatch.setattr(
        all_in_ai_action_bridge.all_in_ai_mission_store,
        "read",
        lambda *_args, **_kwargs: _mission_receipt(),
    )
    monkeypatch.setattr(
        all_in_ai_action_bridge,
        "_review_status",
        lambda *_args, **_kwargs: {
            **_review("APPROVED"), "content_hash": "b" * 64,
        },
    )
    def forbidden(**_kwargs):
        raise AssertionError("unrelated approval must never reach authorization")
    monkeypatch.setattr(
        all_in_ai_action_bridge.governed_action_pipeline,
        "authorize_action",
        forbidden,
    )
    try:
        all_in_ai_action_bridge.handoff_status(
            IDENTITY, MISSION, reviewed_request_id=REQUEST,
        )
    except all_in_ai_action_bridge.ActionHandoffBlocked as exc:
        assert str(exc) == "mission_review_content_mismatch"
    else:
        raise AssertionError("unrelated reviewed input must fail closed")


def test_missing_mission_provenance_blocks_approved_review(monkeypatch):
    monkeypatch.setattr(
        all_in_ai_action_bridge.all_in_ai_mission_store,
        "read",
        lambda *_args, **_kwargs: {
            **_mission_receipt(), "mission_hash": None,
        },
    )
    monkeypatch.setattr(
        all_in_ai_action_bridge,
        "_review_status",
        lambda *_args, **_kwargs: _review("APPROVED"),
    )
    try:
        all_in_ai_action_bridge.handoff_status(
            IDENTITY, MISSION, reviewed_request_id=REQUEST,
        )
    except all_in_ai_action_bridge.ActionHandoffBlocked as exc:
        assert str(exc) == "mission_review_content_mismatch"
    else:
        raise AssertionError("missing Mission hash must not authorize")


def test_bridge_status_creates_no_execution_authority():
    state = all_in_ai_action_bridge.status()
    assert state["execution_authority_created"] is False
    assert state["execution_performed_by_bridge"] is False
    assert state["signed_human_approval_required"] is True
    assert state["human_authority_final"] is True




def _executor_proof(authorization, *, recovery=False):
    return {
        "request_id": authorization["request_id"],
        "approval_receipt_id": authorization["approval_receipt_id"],
        "action_performed": True,
        "evidence_proven": True,
        "status_readback_verified": True,
        "content_unchanged": True,
        "audit_recorded": True,
        "authority_transferred": False,
        "external_side_effect": False,
        "financial_side_effect": False,
        "human_authority_final": True,
        "rollback_verified": recovery,
        "outcome_receipt": {
            "write_verified": True,
            "read_back_verified": True,
            "pipeline_complete": True,
            "human_authority_final": True,
        },
    }


def test_execute_internal_record_requires_authorized_handoff(monkeypatch):
    monkeypatch.setattr(
        all_in_ai_action_bridge,
        "handoff_status",
        lambda *_args, **_kwargs: {
            "mission_id": MISSION,
            "reviewed_request_id": REQUEST,
            "status": "HUMAN_AUTHORITY_REQUIRED",
            "reason": "human_authority_approval_required",
            "execution_authorized": False,
        },
    )

    try:
        all_in_ai_action_bridge.execute_internal_record(
            IDENTITY,
            MISSION,
            reviewed_request_id=REQUEST,
            record_id="00000000-0000-0000-0000-000000000004",
            expected_status="draft",
            target_status="active",
        )
    except all_in_ai_action_bridge.ActionHandoffBlocked as exc:
        assert str(exc) == "human_authority_approval_required"
    else:
        raise AssertionError("execution must remain blocked without approval")


def test_execute_internal_record_uses_server_derived_authorization(monkeypatch):
    authorization = {
        "request_id": REQUEST,
        "approval_receipt_id": "00000000-0000-0000-0000-000000000005",
        "execution_authorized": True,
        "execution_performed": False,
        "human_authority_final": True,
    }
    monkeypatch.setattr(
        all_in_ai_action_bridge,
        "handoff_status",
        lambda *_args, **_kwargs: {
            "mission_id": MISSION,
            "reviewed_request_id": REQUEST,
            "status": "AUTHORIZED_NOT_EXECUTED",
            "authorization": authorization,
        },
    )
    observed = {}

    def _execute(received, **kwargs):
        observed["authorization"] = received
        observed.update(kwargs)
        return _executor_proof(authorization)

    monkeypatch.setattr(
        all_in_ai_action_bridge.internal_record_executor,
        "execute",
        _execute,
    )

    result = all_in_ai_action_bridge.execute_internal_record(
        IDENTITY,
        MISSION,
        reviewed_request_id=REQUEST,
        record_id="00000000-0000-0000-0000-000000000004",
        expected_status="draft",
        target_status="active",
    )

    assert observed["authorization"] is authorization
    assert observed["identity_id"] == IDENTITY
    assert result["execution_performed"] is True
    assert result["outcome_receipt_verified"] is True
    assert result["authority_transferred"] is False
    assert result["human_authority_final"] is True



def test_rollback_internal_record_requires_fresh_authorized_handoff(monkeypatch):
    monkeypatch.setattr(
        all_in_ai_action_bridge,
        "handoff_status",
        lambda *_args, **_kwargs: {
            "mission_id": MISSION,
            "reviewed_request_id": REQUEST,
            "status": "HUMAN_AUTHORITY_REQUIRED",
            "reason": "human_authority_approval_required",
        },
    )

    try:
        all_in_ai_action_bridge.rollback_internal_record(
            IDENTITY,
            MISSION,
            reviewed_request_id=REQUEST,
            rollback_token={
                "record_id": "00000000-0000-0000-0000-000000000004",
                "expected_status": "active",
                "target_status": "draft",
                "before_hash": "a" * 64,
                "after_hash": "b" * 64,
            },
        )
    except all_in_ai_action_bridge.ActionHandoffBlocked as exc:
        assert str(exc) == "human_authority_approval_required"
    else:
        raise AssertionError("rollback must require fresh Human Authority approval")


def test_rollback_internal_record_returns_verified_recovery(monkeypatch):
    authorization = {
        "request_id": REQUEST,
        "approval_receipt_id": "00000000-0000-0000-0000-000000000005",
        "execution_authorized": True,
        "execution_performed": False,
        "human_authority_final": True,
    }
    monkeypatch.setattr(
        all_in_ai_action_bridge,
        "handoff_status",
        lambda *_args, **_kwargs: {
            "mission_id": MISSION,
            "reviewed_request_id": REQUEST,
            "status": "AUTHORIZED_NOT_EXECUTED",
            "authorization": authorization,
        },
    )
    monkeypatch.setattr(
        all_in_ai_action_bridge.internal_record_executor,
        "rollback",
        lambda *_args, **_kwargs: _executor_proof(authorization, recovery=True),
    )

    result = all_in_ai_action_bridge.rollback_internal_record(
        IDENTITY,
        MISSION,
        reviewed_request_id=REQUEST,
        rollback_token={
            "record_id": "00000000-0000-0000-0000-000000000004",
            "expected_status": "active",
            "target_status": "draft",
            "before_hash": "a" * 64,
            "after_hash": "b" * 64,
        },
    )

    assert result["rollback_verified"] is True
    assert result["outcome_receipt_verified"] is True
    assert result["authority_transferred"] is False
    assert result["human_authority_final"] is True


def test_mission_outcome_rejects_unrelated_and_truthy_executor_receipts():
    authorization = {
        "request_id": REQUEST,
        "approval_receipt_id": "00000000-0000-0000-0000-000000000005",
    }
    valid = _executor_proof(authorization)
    assert all_in_ai_action_bridge._verified_executor_outcome(valid, authorization) is True
    assert all_in_ai_action_bridge._verified_executor_outcome(valid, {}) is False
    assert all_in_ai_action_bridge._verified_executor_outcome(
        valid, {**authorization, "approval_receipt_id": None},
    ) is False
    for tampered in (
        {**valid, "request_id": MISSION},
        {**valid, "status_readback_verified": "true"},
        {**valid, "action_performed": 1},
        {**valid, "external_side_effect": None},
        {**valid, "outcome_receipt": {**valid["outcome_receipt"], "read_back_verified": "true"}},
        {**valid, "outcome_receipt": {**valid["outcome_receipt"], "pipeline_complete": None}},
    ):
        assert all_in_ai_action_bridge._verified_executor_outcome(tampered, authorization) is False
    assert all_in_ai_action_bridge._verified_executor_outcome(
        valid, authorization, recovery=True,
    ) is False
    assert all_in_ai_action_bridge._verified_executor_outcome(
        _executor_proof(authorization, recovery=True), authorization, recovery=True,
    ) is True


def test_missing_execution_receipt_never_projects_green_or_automatic_retry(monkeypatch):
    authorization = {
        "request_id": REQUEST,
        "approval_receipt_id": "00000000-0000-0000-0000-000000000005",
    }
    monkeypatch.setattr(
        all_in_ai_action_bridge, "handoff_status",
        lambda *_a, **_k: {
            "mission_id": MISSION,
            "reviewed_request_id": REQUEST,
            "status": "AUTHORIZED_NOT_EXECUTED",
            "authorization": authorization,
        },
    )
    monkeypatch.setattr(
        all_in_ai_action_bridge.internal_record_executor,
        "execute",
        lambda *_a, **_k: {
            "request_id": REQUEST, "action_performed": True,
            "outcome_receipt": {"write_verified": True, "read_back_verified": "true"},
        },
    )
    result = all_in_ai_action_bridge.execute_internal_record(
        IDENTITY, MISSION, reviewed_request_id=REQUEST,
        record_id="00000000-0000-0000-0000-000000000004",
        expected_status="draft", target_status="active",
    )
    assert result["execution_performed"] is True
    assert result["outcome_receipt_verified"] is False
    assert result["execution_evidence_state"] == "RECONCILIATION_REQUIRED"
    assert result["automatic_retry_allowed"] is False
