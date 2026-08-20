from __future__ import annotations

import json

from mission_control import config, organism


def test_canonical_architecture_passes_all_integrity_checks():
    validation = organism.validate_architecture()

    assert validation["passed"] is True
    assert validation["errors"] == []
    assert validation["checks"]["brain_count"] == 1
    assert validation["checks"]["duplicate_systems"] == 0
    assert validation["checks"]["duplicate_names"] == 0
    assert validation["checks"]["overlapping_anatomy_roles"] == 0
    assert validation["checks"]["duplicate_agent_roles"] == 0
    assert validation["checks"]["intelligence_worlds"] == 7
    assert validation["checks"]["registered_agents"] == 25
    assert validation["checks"]["final_authority"] == "Human Authority"


def test_locked_anatomy_and_governance_are_preserved():
    systems = {item["id"]: item for item in organism.ORGANISM_SYSTEMS}
    regions = {item["id"]: item for item in organism.SMI_REGIONS}

    assert systems["smi"]["anatomy"] == "Brain"
    assert systems["living_kernel"]["anatomy"] == "Heart"
    assert systems["nexus"]["anatomy"] == "Nervous system"
    assert systems["living_kernel"]["aliases"] == ("OAP Kernel",)
    assert regions["brainstem"]["kind"] == "bridge"
    assert regions["synthetic_mind"]["kind"] == "internal_organ"
    assert tuple(part["name"] for part in organism.AGENT_ANATOMY) == (
        "Soul",
        "Mind",
        "Body",
    )
    assert [
        (step["actor"], step["action"]) for step in organism.GOVERNANCE_LAW
    ] == [
        ("Intelligence", "proposes"),
        ("Guardian", "protects"),
        ("Builder", "creates"),
        ("Identity", "validates"),
        ("Sovereign", "decides"),
        ("HRM", "remembers"),
        ("Organism", "grows"),
    ]
    sovereign = next(
        step for step in organism.GOVERNANCE_LAW if step["actor"] == "Sovereign"
    )
    assert sovereign["authority"] == "Human Authority"


def test_canonical_projection_excludes_prohibited_and_legacy_names():
    projection = json.dumps(organism.get_public_anatomy())

    assert "Kaa" not in projection
    assert "Council" not in projection
    assert len(organism.INTELLIGENCE_WORLDS) == 7
    assert "Matrix Intelligence" in organism.INTELLIGENCE_WORLDS
    assert "GPT Intelligence" not in organism.INTELLIGENCE_WORLDS
    assert len(set(organism.ADVISORY_AGENTS)) == len(organism.ADVISORY_AGENTS)


def test_every_proposed_refinement_requires_human_approval():
    proposals = organism.get_public_anatomy()["proposed_refinements"]

    assert proposals
    assert all(proposal["requires_human_approval"] is True for proposal in proposals)


def test_duplicate_name_or_second_brain_is_rejected():
    duplicate = {
        **organism.ORGANISM_SYSTEMS[0],
        "id": "duplicate_oasis",
        "aliases": ("NEXUS",),
        "anatomy": "Brain",
    }
    validation = organism.validate_architecture(
        systems=(*organism.ORGANISM_SYSTEMS, duplicate)
    )

    assert validation["passed"] is False
    assert any("Duplicate system names or aliases" in error for error in validation["errors"])
    assert any("one and only brain" in error for error in validation["errors"])


def test_duplicate_agent_roles_are_rejected_before_refinement():
    validation = organism.validate_architecture(
        agent_roles=(
            {"agent": "Neo", "role": "region_advisor"},
            {"agent": "Akela", "role": "region_advisor"},
        )
    )

    assert validation["passed"] is False
    assert any("Duplicate agent roles" in error for error in validation["errors"])


def test_organism_page_is_read_only_and_does_not_create_database(
    client, tmp_path, monkeypatch
):
    database_path = tmp_path / "organism-view.db"
    monkeypatch.setattr(config, "OAP_DATABASE_PATH", str(database_path))

    response = client.get("/mission/organism")

    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Canonical boundaries verified" in page
    assert "Digital Organism Anatomy" in page
    assert "Human approval required" in page
    assert "SMI" in page
    assert "Soul–Mind–Body" in page
    assert "Kaa" not in page
    assert "Council" not in page
    assert not database_path.exists()
    assert client.post("/mission/organism").status_code == 405


def test_smi_cannot_emit_an_independent_execute_decision():
    assert "EXECUTE" not in organism.SMI_OUTPUT_STATES
    assert organism.APPROVED_STATE_PATH.index("HUMAN_APPROVED") < (
        organism.APPROVED_STATE_PATH.index("KERNEL_EXECUTED")
    )
