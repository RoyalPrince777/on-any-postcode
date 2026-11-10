from pathlib import Path

from mission_control import smi_73_signal_field

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "mission_control" / "templates" / "smi_command_dashboard.html"


def test_sovereign_dashboard_uses_canonical_mission_to_100_architecture():
    status = smi_73_signal_field.definition_status()
    assert status["signal_count"] == 73
    assert status["major_dimension_count"] == 21
    assert status["star_gate_count"] == 7
    assert status["reviewer_count"] == 14
    assert status["upgrade_only"] is True
    assert status["truth_mode"] is True


def test_sovereign_dashboard_front_surface_is_low_noise_and_control_first():
    html = TEMPLATE.read_text(encoding="utf-8")
    required = (
        "Sovereign Megaverse Intelligence",
        "Your intelligence, visible without the noise.",
        "Essential controls",
        "SMI Character",
        "Movement Intelligence",
        "Learning Intelligence",
        "War Room",
        "Mission to 100",
        "Live excluded",
        "Human Authority final",
    )
    for phrase in required:
        assert phrase in html

    # The old telecom/graphs/monitors blocks remain available in backend evidence
    # but must not dominate the sovereign front surface.
    assert ">Graphs<" not in html
    assert ">Monitors<" not in html
    assert "Telecom truth review" not in html


def test_sovereign_dashboard_preserves_one_front_door_and_deeper_systems():
    html = TEMPLATE.read_text(encoding="utf-8")
    for route in (
        "/mission/smi",
        "/mission/war-room",
        "/mission/agents",
        "/movement",
        "/mission/brain",
    ):
        assert route in html
    assert "ONE WORLD · ONE FRONT DOOR · MANY SYSTEMS INSIDE" in html
