"""Mission-to-100 protocol locks for SMI Archive."""
from mission_control import smi_archive


def test_mission_to_100_requires_exact_artifact_parity_and_human_final():
    status = smi_archive.status()
    rules = {item["id"]: item["rule"] for item in status["mission_to_100_protocol"]}

    assert status["exact_artifact_parity_required_for_production_green"] is True
    assert status["mandatory_gate_can_be_averaged_away"] is False
    assert "artifact" in rules["exact-artifact-parity"].lower()
    assert "target" in rules["target-runtime-proof"].lower()
    assert "averaged" in rules["no-average-away"].lower()
    assert "recovery" in rules["rollback-before-promotion"].lower()
    assert status["human_authority_final"] is True


def test_mission_to_100_protocol_is_not_a_new_authority_or_brain():
    status = smi_archive.status()

    assert status["new_brain_created"] is False
    assert status["new_memory_engine_created"] is False
    assert status["new_execution_authority_created"] is False
    assert status["history_is_timeline_inside_archive"] is True


def test_smi_only_noise_free_upgrade_protocol():
    rules = {
        item["id"]: item["rule"]
        for item in smi_archive.status()["mission_to_100_protocol"]
    }
    assert "first-party SMI brain" in rules["first-party-smi-only"]
    assert "existing PR" in rules["no-duplicate-work"]
    assert "Truth Mode" in rules["truth-adversarial-review"]
    assert "not independent agents" in rules["truth-adversarial-review"]
    assert "denominator" in rules["no-cosmetic-percentages"]
    assert "Unknown" in rules["no-cosmetic-percentages"]
