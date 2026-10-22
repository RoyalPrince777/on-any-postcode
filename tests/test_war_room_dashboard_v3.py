from __future__ import annotations

import json

from mission_control import agents, config, organism, war_room


def _ratings(projection):
    return [item for category in projection["categories"] for item in category["items"]]


def test_war_room_rates_every_world_and_digital_organ():
    projection = war_room.get_war_room_dashboard()
    ratings = _ratings(projection)
    ids = {item["id"] for item in ratings}

    assert projection["validation"]["passed"] is True
    assert projection["validation"]["checks"]["rated_areas"] >= 47
    assert {f"world_{world['id']}" for world in agents.INTELLIGENCE_WORLDS} <= ids
    assert {f"organ_{organ['id']}" for organ in organism.BODY_ORGANS} <= ids
    assert {
        "identity_authority", "smi_brain", "agent_registry", "postgres_hrm",
        "organism_runtime", "home_node", "oap_os_install_shell", "route_core",
        "rtl_guardian_nexus", "rtl_memory_guard", "rtl_attestation",
        "fpga_reference", "physical_oap_silicon",
    } <= ids


def test_star_ratings_are_sequential_and_never_skip_missing_evidence():
    projection = war_room.get_war_room_dashboard()
    for item in _ratings(projection):
        stages = item["stages"]
        assert len(stages) == 5
        prefix = 0
        for index, stage in enumerate(stages):
            if not stage["passed"] or prefix != index:
                break
            prefix += 1
        assert item["stars"] == prefix
        assert item["score"] is None
        assert item["assessment_basis"] == "advisory_stage_flags"
        assert item["release_evidence_verified"] is False
        assert item["human_approval_required"] is True
        assert len(item["stars_display"]) == 5

    physical = next(item for item in _ratings(projection) if item["id"] == "physical_oap_silicon")
    assert physical["stars"] == 1
    assert "No fabricated OAP chip" in physical["truth_boundary"]


def test_war_room_top_three_are_impact_and_runtime_gates():
    projection = war_room.get_war_room_dashboard()
    assert [item["id"] for item in projection["top_next"]] == [
        "identity_authority", "postgres_hrm", "live_product_certification",
    ]
    assert all(item["impact"] == 5 for item in projection["top_next"])
    assert all(item["human_approval_required"] for item in projection["top_next"])


def test_identity_cannot_reach_runtime_verified_without_active_authority(monkeypatch):
    monkeypatch.setattr(war_room.neon_auth, "status", lambda: {"configured": True, "valid": True})
    monkeypatch.setattr(war_room.postgres_db, "postgres_status", lambda: {
        "reachable": True, "initialized": True, "checksum_mismatches": [],
    })
    monkeypatch.setattr(war_room.authority, "status", lambda: {
        "database_reachable": True, "active_level_zero": False,
        "approval_permission": False, "ready": False,
    })
    identity = next(item for item in _ratings(war_room.get_war_room_dashboard()) if item["id"] == "identity_authority")
    assert identity["stars"] == 3
    assert identity["first_missing_stage"] == "Runtime verified"


def test_war_room_conflict_gate_detects_no_active_duplicates_or_kaa():
    audit = war_room.get_war_room_dashboard()["conflict_audit"]
    assert audit["passed"] is True
    assert audit["active_conflict_count"] == 0
    assert audit["duplicate_systems"] == 0
    assert audit["duplicate_agent_ids"] == 0
    assert audit["duplicate_agent_roles"] == 0
    assert audit["naming_conflicts"] == 0
    assert audit["kaa_registered"] is False
    assert any(boundary["components"] == "Colonel Hathi / Hathi" for boundary in audit["resolved_boundaries"])


def test_war_room_dashboard_is_founder_only_read_only_and_does_not_create_db(
    client, anonymous_client, tmp_path, monkeypatch
):
    database_path = tmp_path / "war-room.db"
    monkeypatch.setattr(config, "OAP_DATABASE_PATH", str(database_path))
    response = client.get("/mission/war-room")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "Founder-only · Research Intelligence" in page
    assert "Research intelligence" in page
    assert "7× DEEP DIVE" in page
    assert "This surface performs no production write" in page
    assert "Human Authority remains final" in page
    assert 'method="post"' not in page.lower()
    assert client.post("/mission/war-room").status_code == 405
    assert anonymous_client.get("/mission/war-room").status_code == 302
    assert anonymous_client.get("/mission/war-room/status").status_code == 401
    assert not database_path.exists()


def test_master_war_room_page_locks_canonical_seven_x_and_seven_star_contract(client):
    response = client.get("/mission/war-room")
    page = response.get_data(as_text=True)
    assert response.status_code == 200

    for checkpoint in (
        "1 · Discovery", "2 · Verification", "3 · Alternatives", "4 · Adversarial",
        "5 · Systems", "6 · Consequence", "7 · Synthesis",
    ):
        assert checkpoint in page
    for star in ("Truth", "Function", "Security", "Stability", "Integration", "Compliance", "Learning"):
        assert star in page
    for required in (
        "Observe → Classify → Verify → Fix/Plan → Retest → Record → Learn",
        "No evidence = no Green. No test = no star.",
        "No fabricated tally",
        "Challenge room",
        "Guardian · End Review · SMI Judgement",
        "Clear output",
    ):
        assert required in page
    assert 'method="post"' not in page.lower()
    assert "This surface performs no production write" in page


def test_war_room_status_is_redacted_and_preserves_human_authority(client):
    response = client.get("/mission/war-room/status")
    payload = response.get_json()
    serialized = response.get_data(as_text=True).lower()
    assert response.status_code == 200
    assert payload["controls_enabled"] is False
    assert payload["can_approve"] is False
    assert payload["can_execute"] is False
    assert payload["validation"]["checks"]["final_authority"] == "Human Authority"
    assert payload["human_authority"]["status"] == "Final approval required"
    assert json.dumps(payload).count("Human Authority") >= 1
    for private_key in ("password", "secret", "private_key", "database_url", "correlation_id", "message_body"):
        assert private_key not in serialized
    assert '"kaa"' not in serialized
    assert "council" not in serialized


def test_mission_navigation_links_to_war_room(client):
    for path in ("/mission", "/mission/brain", "/mission/organism"):
        page = client.get(path).get_data(as_text=True)
        assert 'href="/mission/war-room"' in page


def test_dashboard_never_turns_advisory_flags_into_completion_or_certification(client):
    response = client.get("/mission/war-room/status")
    assert response.status_code == 200
    payload = response.get_json()
    summary = payload["summary"]
    for name in ("overall_evidence_score", "vpi_percent", "runtime_verified",
                 "operationally_certified"):
        assert summary[name] is None
    assert summary["acceptance_inventory_verified"] is False
    for category in payload["categories"]:
        assert category["runtime_verified"] is None
        assert category["certified"] is None
    evidence = payload["mission_evidence"]
    assert evidence["judge_votes"] is None
    assert evidence["revision"] is None
    assert evidence["full_green"] is False
    assert len(evidence["proof_dimensions"]) == 7
    assert not any(d["star_awarded"] for d in evidence["proof_dimensions"])

    page = client.get("/mission/war-room").get_data(as_text=True)
    assert "VPI: N/A" in page
    assert "None%" not in page
    assert 'aria-label="Overall evidence score"' not in page
    for dimension in evidence["proof_dimensions"]:
        assert f'data-proof-dimension="{dimension["name"]}" data-proof-status="not_verified"' in page
    assert page.count("Not verified · no star awarded") == 7
    assert "Passing software tests do not prove live booking, dispatch or payments" in page
    assert "not mandatory stages or repeated approval stops" in page


def test_all_advisory_stages_passed_cannot_claim_release_green():
    result = war_room._rating(
        item_id="test", name="All supplied flags", category="test", summary="test",
        stages=tuple({"stage": name, "passed": True, "evidence": "supplied flag"}
                     for name in ("scope", "code", "tests", "runtime", "operations")),
        next_gate="Authenticated release evidence", impact=5,
    )
    assert result["stars"] == 5
    assert result["label"].startswith("Advisory · ")
    assert result["signal"] == "purple"
    assert result["score"] is None
    assert result["release_evidence_verified"] is False
    assert result["human_approval_required"] is True


def test_summary_consumers_preserve_unknown_instead_of_converting_to_zero(client, csrf):
    action_response = client.post(
        "/mission/war-room/actions/status", json={}, headers={"X-OAP-CSRF": csrf["csrf_token"]},
    )
    assert action_response.status_code == 200
    action = action_response.get_json()["war_room"]
    command = client.get("/mission/smi/status").get_json()["war_room"]
    for summary in (command, action):
        for name in ("overall_evidence_score", "runtime_verified", "operationally_certified"):
            assert summary[name] is None
