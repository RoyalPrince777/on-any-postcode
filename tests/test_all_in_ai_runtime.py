import pytest

from mission_control import all_in_ai_runtime


def test_runtime_reuses_single_smi_brain_and_general_intelligence_spine():
    state = all_in_ai_runtime.status()
    assert state["ready"] is True
    assert state["brain_count_added"] == 0
    assert state["single_smi_brain_preserved"] is True
    assert state["agi_core_ready"] is True
    assert state["general_intelligence_capabilities"] == 15
    assert state["independent_execute"] is False
    assert state["independent_approval"] is False
    assert state["human_authority_final"] is True


def test_mission_routes_through_existing_agi_and_command_intelligence():
    plan = all_in_ai_runtime.plan_mission(
        "Deep dive OAP Maps movement routing and recovery",
        task_type="TECHNICAL",
    )
    binding = plan["smi_binding"]
    assert binding["brain_count_added"] == 0
    assert binding["single_smi_brain_preserved"] is True
    assert "movement" in binding["agi_route"]["world_ids"]
    assert binding["command_review"]["core_path"][0] == "agi"
    assert binding["command_review"]["command_path"] == (
        "sgi",
        "tgi",
        "ogi",
        "dgi",
        "pgi",
        "rgi",
        "adgi",
        "mgi",
    )
    assert plan["red_team"]["fail_closed_without_evidence"] is True
    assert plan["truth_mode"]["execution_granted"] is False
    assert plan["authority"]["founder_final"] is True


def test_alien_research_mode_stays_speculative_and_non_executing():
    plan = all_in_ai_runtime.plan_mission(
        "Explore an unconventional future communications architecture",
        research_mode="alien_research",
    )
    assert plan["alien_research"]["active"] is True
    assert plan["alien_research"]["claims_fact_without_evidence"] is False
    assert plan["alien_research"]["requires_truth_mode_evidence"] is True
    assert plan["alien_research"]["execution_authority"] is False


@pytest.mark.parametrize("mission", ["", "   ", None])
def test_empty_mission_fails_closed(mission):
    with pytest.raises(ValueError, match="mission_required"):
        all_in_ai_runtime.plan_mission(mission)


def test_unknown_research_mode_fails_closed():
    with pytest.raises(ValueError, match="unsupported_research_mode"):
        all_in_ai_runtime.plan_mission("test", research_mode="magic")


def test_start_mission_hashes_prompt_and_persists_without_raw_text(monkeypatch):
    captured = {}

    def fake_create(identity_id, *, mission_id, mission_hash, plan):
        captured.update(
            identity_id=identity_id,
            mission_id=mission_id,
            mission_hash=mission_hash,
            plan=plan,
        )
        return {
            "mission_id": mission_id,
            "state": "planned",
            "digest": "a" * 64,
            "read_back_verified": True,
            "audit_verified": True,
            "hrm_verified": True,
        }

    monkeypatch.setattr(all_in_ai_runtime.all_in_ai_mission_store, "create", fake_create)
    result = all_in_ai_runtime.start_mission(
        "00000000-0000-0000-0000-000000000001",
        "Secret Founder mission text",
        task_type="STRATEGY",
    )
    assert result["raw_mission_retained"] is False
    assert result["execution_granted"] is False
    assert captured["identity_id"] == "00000000-0000-0000-0000-000000000001"
    assert captured["mission_hash"] != "Secret Founder mission text"
    assert len(captured["mission_hash"]) == 64
    assert "Secret Founder mission text" not in repr(captured["plan"])


def test_runtime_stop_and_recover_delegate_to_durable_store(monkeypatch):
    calls = []

    def fake_stop(identity_id, mission_id, *, expected_previous_hash):
        calls.append(("stop", identity_id, mission_id, expected_previous_hash))
        return {"state": "stopped", "execution_granted": False}

    def fake_recover(identity_id, mission_id, *, expected_previous_hash):
        calls.append(("recover", identity_id, mission_id, expected_previous_hash))
        return {"state": "recovered", "execution_granted": False}

    monkeypatch.setattr(all_in_ai_runtime.all_in_ai_mission_store, "stop", fake_stop)
    monkeypatch.setattr(
        all_in_ai_runtime.all_in_ai_mission_store,
        "recover",
        fake_recover,
    )
    identity = "00000000-0000-0000-0000-000000000001"
    mission = "00000000-0000-0000-0000-000000000002"
    stopped = all_in_ai_runtime.stop_mission(
        identity,
        mission,
        expected_previous_hash="1" * 64,
    )
    recovered = all_in_ai_runtime.recover_mission(
        identity,
        mission,
        expected_previous_hash="2" * 64,
    )
    assert stopped["state"] == "stopped"
    assert recovered["state"] == "recovered"
    assert calls == [
        ("stop", identity, mission, "1" * 64),
        ("recover", identity, mission, "2" * 64),
    ]


def test_runtime_status_exposes_durable_nonexecuting_store():
    state = all_in_ai_runtime.status()
    store = state["durable_mission_store"]
    assert store["canonical_workspace_reused"] == "governance"
    assert store["canonical_hrm_reused"] is True
    assert store["canonical_audit_chain_reused"] is True
    assert store["new_database_created"] is False
    assert store["schema_migration_required"] is False
    assert store["raw_mission_retained"] is False
    assert store["execution_granted"] is False
