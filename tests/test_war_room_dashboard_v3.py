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
        "identity_authority",
        "smi_brain",
        "agent_registry",
        "postgres_hrm",
        "organism_runtime",
        "home_node",
        "route_core",
        "rtl_guardian_nexus",
        "rtl_memory_guard",
        "rtl_attestation",
        "fpga_reference",
        "physical_oap_silicon",
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
        assert item["score"] == item["stars"] * 20
        assert len(item["stars_display"]) == 5

    physical = next(
        item for item in _ratings(projection) if item["id"] == "physical_oap_silicon"
    )
    assert physical["stars"] == 1
    assert "No fabricated OAP chip" in physical["truth_boundary"]


def test_war_room_top_three_are_impact_and_runtime_gates():
    projection = war_room.get_war_room_dashboard()

    assert [item["id"] for item in projection["top_next"]] == [
        "identity_authority",
        "postgres_hrm",
        "live_product_certification",
    ]
    assert all(item["impact"] == 5 for item in projection["top_next"])
    assert all(item["human_approval_required"] for item in projection["top_next"])


def test_war_room_conflict_gate_detects_no_active_duplicates_or_kaa():
    audit = war_room.get_war_room_dashboard()["conflict_audit"]

    assert audit["passed"] is True
    assert audit["active_conflict_count"] == 0
    assert audit["duplicate_systems"] == 0
    assert audit["duplicate_agent_ids"] == 0
    assert audit["duplicate_agent_roles"] == 0
    assert audit["naming_conflicts"] == 0
    assert audit["kaa_registered"] is False
    assert any(
        boundary["components"] == "Colonel Hathi / Hathi"
        for boundary in audit["resolved_boundaries"]
    )


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
    assert "OAP War Room" in page
    assert "Highest-value next three" in page
    assert "78 Agent Passports" in page
    assert "RTL Memory Guard / IOMMU" in page
    assert "RTL Trust / Attestation" in page
    assert "Physical OAP Silicon" in page
    assert "No approve, execute, deploy, migrate, purchase, flash or activate" in page
    assert 'method="post"' not in page.lower()
    assert client.post("/mission/war-room").status_code == 405
    assert anonymous_client.get("/mission/war-room").status_code == 302
    assert anonymous_client.get("/mission/war-room/status").status_code == 401
    assert not database_path.exists()


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
    for private_key in (
        "password",
        "secret",
        "private_key",
        "database_url",
        "correlation_id",
        "message_body",
    ):
        assert private_key not in serialized
    assert '"kaa"' not in serialized
    assert "council" not in serialized


def test_mission_navigation_links_to_war_room(client):
    for path in ("/mission", "/mission/brain", "/mission/organism"):
        page = client.get(path).get_data(as_text=True)
        assert 'href="/mission/war-room"' in page
