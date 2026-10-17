from __future__ import annotations

from mission_control import smi_master_blueprint_101


def test_master_blueprint_101_has_exact_canonical_breadth():
    status = smi_master_blueprint_101.status()
    validation = status["validation"]

    assert status["item_count"] == 101
    assert validation["item_count"] == 101
    assert validation["unique_id_count"] == 101
    assert validation["passed"] is True
    assert validation["errors"] == ()
    assert validation["progress_stage_count"] == 0
    assert validation["is_progress_ladder"] is False
    assert validation["category_counts"] == {
        "command_center_home": 11,
        "mission_links": 7,
        "core_functions": 13,
        "core_review_signals": 21,
        "intelligence_lenses": 26,
        "interaction_surfaces": 9,
        "autonomy_levels": 7,
        "infrastructure_modules": 4,
        "governance_locks": 3,
    }


def test_master_blueprint_101_reuses_existing_canonical_registries():
    items = smi_master_blueprint_101.MASTER_BLUEPRINT_101
    categories = {}
    for item in items:
        categories.setdefault(item["category"], []).append(item)

    assert len(categories["command_center_home"]) == 11
    assert len(categories["mission_links"]) == 7
    assert len(categories["core_functions"]) == 13
    assert len(categories["core_review_signals"]) == 21
    assert len(categories["intelligence_lenses"]) == 26
    assert len(categories["interaction_surfaces"]) == 9
    assert len(categories["autonomy_levels"]) == 7
    assert len(categories["infrastructure_modules"]) == 4
    assert len(categories["governance_locks"]) == 3


def test_master_blueprint_101_preserves_founder_protocol_and_authority():
    status = smi_master_blueprint_101.status()
    protocol = status["protocol"]
    authority = status["authority"]

    assert protocol["101_is_architecture_breadth"] is True
    assert protocol["101_is_progress_stages"] is False
    assert all(
        protocol[key] is True
        for key in (
            "unnecessary_stages_removed",
            "repeated_status_loops_removed",
            "demos_as_progress_removed",
            "simulation_when_real_proof_exists_removed",
            "duplicate_reports_removed",
            "repeated_approval_prompts_removed",
            "cosmetic_percentage_inflation_removed",
            "stop_after_every_small_fix_removed",
        )
    )
    assert authority == {
        "execution_granted": False,
        "approval_granted": False,
        "autonomy_expanded": False,
        "human_authority_final": True,
    }


def test_master_blueprint_101_route_is_founder_only(client, anonymous_client):
    response = client.get("/mission/smi/master-blueprint-101")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["component"] == "SMI Full Master Blueprint 101"
    assert payload["item_count"] == 101
    assert payload["validation"]["passed"] is True
    assert response.headers["Cache-Control"] == "no-store"

    anonymous = anonymous_client.get("/mission/smi/master-blueprint-101")
    assert anonymous.status_code == 401
