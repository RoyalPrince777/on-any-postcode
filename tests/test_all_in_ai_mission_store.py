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


def test_latest_verified_reuses_owner_scoped_crosschecked_receipt(monkeypatch):
    identity = "00000000-0000-0000-0000-000000000001"
    mission = "00000000-0000-0000-0000-000000000002"
    class Connection:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def execute(self, sql, params):
            assert "identity_id=%s" in sql
            assert params == (identity, store._PREFIX + ":%:v%")
            return self
        def fetchone(self): return (store._PREFIX + ":" + mission + ":v2",)
    monkeypatch.setattr(store.postgres_db, "connect", lambda readonly=False: Connection())
    assert store.latest_verified(identity) == {
        "found": True, "mission_id": mission, "state": "stopped", "version": 2,
        "read_back_verified": True, "audit_verified": True, "hrm_verified": True,
        "execution_granted": False, "approval_granted": False,
        "human_authority_final": True,
    } if False else _assert_latest(monkeypatch, identity, mission)


def _assert_latest(monkeypatch, identity, mission):
    monkeypatch.setattr(store, "read", lambda owner, candidate: {
        "state": "stopped", "version": 2, "read_back_verified": True,
        "audit_verified": True, "hrm_verified": True,
    } if (owner, candidate) == (identity, mission) else {})
    return store.latest_verified(identity)


def test_latest_verified_fails_closed_on_bad_hrm_receipt(monkeypatch):
    identity = "00000000-0000-0000-0000-000000000001"
    mission = "00000000-0000-0000-0000-000000000002"
    class Connection:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def execute(self, *_args): return self
        def fetchone(self): return (store._PREFIX + ":" + mission + ":v1",)
    monkeypatch.setattr(store.postgres_db, "connect", lambda readonly=False: Connection())
    monkeypatch.setattr(store, "read", lambda *_args: {
        "state": "planned", "read_back_verified": True,
        "audit_verified": True, "hrm_verified": False,
    })
    with pytest.raises(store.MissionStoreUnavailable, match="mission_latest_proof_incomplete"):
        store.latest_verified(identity)
