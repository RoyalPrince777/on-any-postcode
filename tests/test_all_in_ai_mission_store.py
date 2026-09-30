import pytest

from mission_control import all_in_ai_mission_store as store


def _plan():
    return {
        "mission": {
            "task_type": "TECHNICAL",
            "high_impact": False,
            "research_mode": "standard",
            "length": 42,
        },
        "smi_binding": {
            "agi_route": {
                "world_ids": ("matrix", "movement"),
                "specialist_ids": ("multimodal",),
            },
            "command_review": {
                "command_path": (
                    "sgi",
                    "tgi",
                    "ogi",
                    "dgi",
                    "pgi",
                    "rgi",
                    "adgi",
                    "mgi",
                ),
                "war_room_next": True,
                "judgement_next": True,
            },
        },
    }


def test_safe_plan_snapshot_is_privacy_minimised():
    snapshot = store._safe_plan_snapshot(_plan())
    assert snapshot["prompt_retained"] is False
    assert snapshot["execution_granted"] is False
    assert snapshot["approval_granted"] is False
    assert snapshot["human_authority_final"] is True
    assert snapshot["world_ids"] == ("matrix", "movement")
    assert "prompt" not in snapshot
    assert "mission" not in snapshot


def test_receipt_digest_detects_state_change():
    payload = {
        "mission_id": "00000000-0000-0000-0000-000000000002",
        "version": 1,
        "state": "planned",
    }
    one = store._digest(payload)
    two = store._digest({**payload, "state": "stopped"})
    assert len(one) == 64
    assert one != two


def test_store_status_reuses_canonical_persistence_without_migration():
    state = store.status()
    assert state["canonical_workspace_reused"] == "governance"
    assert state["canonical_hrm_reused"] is True
    assert state["canonical_audit_chain_reused"] is True
    assert state["new_database_created"] is False
    assert state["schema_migration_required"] is False
    assert state["raw_mission_retained"] is False
    assert state["stop_supported"] is True
    assert state["recovery_supported"] is True


def test_stop_is_idempotent_when_already_stopped(monkeypatch):
    current = {
        "state": "stopped",
        "mission_hash": "a" * 64,
        "plan": {},
        "digest": "b" * 64,
    }
    monkeypatch.setattr(store, "read", lambda *_args, **_kwargs: current)

    def fail_append(*_args, **_kwargs):
        raise AssertionError("idempotent STOP must not append")

    monkeypatch.setattr(store, "_append", fail_append)
    assert store.stop(
        "00000000-0000-0000-0000-000000000001",
        "00000000-0000-0000-0000-000000000002",
        expected_previous_hash="b" * 64,
    ) == current


def test_recovery_requires_durable_stop(monkeypatch):
    monkeypatch.setattr(
        store,
        "read",
        lambda *_args, **_kwargs: {
            "state": "planned",
            "mission_hash": "a" * 64,
            "plan": {},
            "digest": "b" * 64,
        },
    )
    with pytest.raises(RuntimeError, match="mission_not_stopped"):
        store.recover(
            "00000000-0000-0000-0000-000000000001",
            "00000000-0000-0000-0000-000000000002",
            expected_previous_hash="b" * 64,
        )


def _latest_record_connection(monkeypatch, identity, mission, *, version=2, record_id="record-2",
                              title=None):
    title = title if title is not None else f"{store._PREFIX}:{mission}:v{version}"
    class Connection:
        def __enter__(self): return self
        def __exit__(self, *_args): return False
        def execute(self, sql, params):
            assert "SELECT record_id,title" in sql
            assert "identity_id=%s" in sql
            assert params == (identity, store._PREFIX + ":%:v%")
            return self
        def fetchone(self): return (record_id, title)
    monkeypatch.setattr(store.postgres_db, "connect", lambda readonly=False: Connection())


def test_latest_verified_reuses_owner_scoped_crosschecked_receipt(monkeypatch):
    identity = "00000000-0000-0000-0000-000000000001"
    mission = "00000000-0000-0000-0000-000000000002"
    _latest_record_connection(monkeypatch, identity, mission)
    monkeypatch.setattr(store, "read", lambda owner, candidate: {
        "mission_id": mission, "record_id": "record-2",
        "state": "stopped", "version": 2, "read_back_verified": True,
        "audit_verified": True, "hrm_verified": True,
    } if (owner, candidate) == (identity, mission) else {})
    assert store.latest_verified(identity) == {
        "found": True, "mission_id": mission, "state": "stopped", "version": 2,
        "read_back_verified": True, "audit_verified": True, "hrm_verified": True,
        "execution_granted": False, "approval_granted": False,
        "human_authority_final": True,
    }


def test_latest_verified_fails_closed_on_bad_hrm_receipt(monkeypatch):
    identity = "00000000-0000-0000-0000-000000000001"
    mission = "00000000-0000-0000-0000-000000000002"
    _latest_record_connection(monkeypatch, identity, mission, version=1)
    monkeypatch.setattr(store, "read", lambda *_args: {
        "mission_id": mission, "record_id": "record-2",
        "state": "planned", "version": 1, "read_back_verified": True,
        "audit_verified": True, "hrm_verified": False,
    })
    with pytest.raises(store.MissionStoreUnavailable, match="mission_latest_proof_incomplete"):
        store.latest_verified(identity)


@pytest.mark.parametrize("override", [
    {"record_id": "different-record"},
    {"version": 3},
    {"version": True},
    {"mission_id": "00000000-0000-0000-0000-000000000003"},
])
def test_latest_verified_rejects_changed_or_inconsistent_receipt(monkeypatch, override):
    identity = "00000000-0000-0000-0000-000000000001"
    mission = "00000000-0000-0000-0000-000000000002"
    _latest_record_connection(monkeypatch, identity, mission)
    receipt = {
        "mission_id": mission, "record_id": "record-2", "version": 2,
        "state": "planned", "read_back_verified": True,
        "audit_verified": True, "hrm_verified": True,
        **override,
    }
    monkeypatch.setattr(store, "read", lambda *_args: receipt)
    with pytest.raises(store.MissionStoreUnavailable, match="mission_latest_changed"):
        store.latest_verified(identity)


@pytest.mark.parametrize("bad_title", [
    "OAP-ALL-IN-AI:invalid:v2",
    "OAP-ALL-IN-AI:00000000-0000-0000-0000-000000000002:v0",
    "OAP-ALL-IN-AI:00000000-0000-0000-0000-000000000002:v02",
    "OAP-ALL-IN-AI:00000000-0000-0000-0000-000000000002:v2:extra",
])
def test_latest_verified_rejects_noncanonical_title_before_read(monkeypatch, bad_title):
    identity = "00000000-0000-0000-0000-000000000001"
    mission = "00000000-0000-0000-0000-000000000002"
    _latest_record_connection(monkeypatch, identity, mission, title=bad_title)
    monkeypatch.setattr(store, "read", lambda *_args: pytest.fail("invalid title must not read"))
    with pytest.raises(store.MissionStoreUnavailable, match="mission_latest_invalid"):
        store.latest_verified(identity)


def test_mission_inference_receipt_correlates_owned_plaintext_hrm_only(monkeypatch):
    identity = "00000000-0000-0000-0000-000000000001"
    mission = "00000000-0000-0000-0000-000000000002"
    request = "00000000-0000-0000-0000-000000000003"
    monkeypatch.setattr(store, "read", lambda owner, item: {
        "state": "planned", "mission_hash": "a" * 64,
        "read_back_verified": True, "audit_verified": True, "hrm_verified": True,
    } if (owner, item) == (identity, mission) else {})
    rows = [[
        "a" * 64, "RECOMMENDATION_READY",
        ["RECEIVED", "PROVIDER_COMPLETED", "HRM_RECORDED"],
        {"image_attached": False, "media_kind": None, "code_proposal": False},
    ]]
    class Connection:
        def __enter__(self): return self
        def __exit__(self, *_args): return False
        def execute(self, sql, params):
            assert "identity_id=%s AND request_id=%s" in sql
            assert params == (identity, request)
            return self
        def fetchone(self): return rows[0]
    monkeypatch.setattr(store.postgres_db, "connect", lambda readonly=False: Connection())
    outcome = store.inference_receipt_evidence(identity, mission, request)
    assert outcome["mission_text_hash_matched"] is True
    assert outcome["governed_response_recorded"] is True
    assert outcome["first_party_inference_proven"] is False
    assert outcome["mission_execution_proven"] is False
    assert outcome["approval_granted"] is False
    assert outcome["human_authority_final"] is True
    rows[0] = ["b" * 64, *rows[0][1:]]
    with pytest.raises(store.MissionStoreUnavailable, match="mission_inference_hash_mismatch"):
        store.inference_receipt_evidence(identity, mission, request)
    rows[0] = ["a" * 64, "REVIEW_REQUIRED", ["HRM_RECORDED"], rows[0][3]]
    with pytest.raises(store.MissionStoreUnavailable, match="mission_inference_proof_incomplete"):
        store.inference_receipt_evidence(identity, mission, request)


def test_mission_inference_receipt_rejects_stopped_checkpoint_before_query(monkeypatch):
    monkeypatch.setattr(store, "read", lambda *_args: {"state": "stopped"})
    def forbidden(*_args, **_kwargs):
        raise AssertionError("stopped mission must not query inference")
    monkeypatch.setattr(store.postgres_db, "connect", forbidden)
    with pytest.raises(store.MissionStoreUnavailable, match="mission_stopped"):
        store.inference_receipt_evidence(
            "00000000-0000-0000-0000-000000000001",
            "00000000-0000-0000-0000-000000000002",
            "00000000-0000-0000-0000-000000000003",
        )
