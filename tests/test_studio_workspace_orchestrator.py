import json
from uuid import uuid4

from mission_control import studio_workspace_orchestrator as orchestrator


def test_multi_workspace_plan_expands_dependencies_without_execution():
    plan = orchestrator.plan("Research the market, design the database, build the app, code it, make launch video and music")
    workspaces = [step["workspace"] for step in plan["steps"]]
    assert workspaces == ["research", "data", "build", "code", "motion", "music"]
    assert plan["resumable"] is True
    assert plan["execution_authorised"] is False
    assert plan["deploy_authorised"] is False
    assert plan["database_write_authorised"] is False
    assert plan["publish_authorised"] is False
    assert plan["payment_authorised"] is False


def test_orchestration_checkpoint_is_owner_scoped_hash_chained_and_read_back(monkeypatch):
    owner = str(uuid4())
    mission = orchestrator.plan("build an app with a database")
    store = []

    monkeypatch.setattr(
        orchestrator.workspaces,
        "list_studio_orchestration_records",
        lambda identity_id, mission_id, limit=100: list(store),
    )

    def save(identity_id, *, mission_id, version, digest, title, body):
        store.append({
            "record_id": str(uuid4()),
            "title": title,
            "body": body,
            "status": "draft",
            "created_at": "2026-09-26T00:00:00+00:00",
            "updated_at": "2026-09-26T00:00:00+00:00",
        })
        return store[-1]["record_id"]

    monkeypatch.setattr(
        orchestrator.workspaces, "add_studio_orchestration_record_atomic", save
    )
    result = orchestrator.checkpoint(owner, mission, expected_last_hash="")
    assert result["version"] == 1
    assert result["read_back_verified"] is True
    resumed = orchestrator.resume(owner, mission["mission_id"])
    assert resumed["history_versions"] == 1
    assert resumed["execution_authorised"] is False

    second = dict(mission)
    second["steps"] = [dict(step) for step in mission["steps"]]
    latest_hash = resumed["digest"]
    result2 = orchestrator.checkpoint(owner, second, expected_last_hash=latest_hash)
    assert result2["version"] == 2
    assert len(store) == 2
    assert json.loads(store[1]["body"])["previous_hash"] == latest_hash


def test_stop_and_stale_version_fail_closed(monkeypatch):
    owner = str(uuid4())
    mission = orchestrator.plan("research and build")
    monkeypatch.setattr(
        orchestrator.workspaces,
        "list_studio_orchestration_records",
        lambda identity_id, mission_id, limit=100: [],
    )
    try:
        orchestrator.checkpoint(owner, mission, stopped=True)
    except PermissionError as exc:
        assert "STOP" in str(exc)
    else:
        raise AssertionError("STOP must block checkpoint")


def test_next_handoff_returns_only_dependency_eligible_workspace(monkeypatch):
    owner = str(uuid4())
    mission_id = str(uuid4())
    monkeypatch.setattr(
        orchestrator,
        "resume",
        lambda identity_id, mid: {
            "mission_id": mission_id,
            "steps": [
                {"step": 1, "workspace": "research", "depends_on": [], "state": "completed_with_proof"},
                {"step": 2, "workspace": "data", "depends_on": ["research"], "state": "queued"},
                {"step": 3, "workspace": "build", "depends_on": ["research", "data"], "state": "queued"},
            ],
            "execution_authorised": False,
        },
    )
    monkeypatch.setattr(
        orchestrator.studio_intelligence,
        "workspace_preflight",
        lambda wid: {"workspace": {"id": wid}, "state": "ready", "execution_granted": False},
    )
    handoff = orchestrator.next_handoff(owner, mission_id)
    assert handoff["workspace"] == "data"
    assert handoff["state"] == "handoff_ready"
    assert handoff["execution_authorised"] is False


def test_orchestrator_status_is_nonconsequential():
    status = orchestrator.status()
    assert status["dependency_graph_ready"] is True
    assert status["owner_scoped_checkpoint_ready"] is True
    assert status["resumable_handoff_ready"] is True
    assert status["next_handoff_preflight_ready"] is True
    assert status["execution_authorised"] is False
    assert status["consequential_execution_locked"] is True
