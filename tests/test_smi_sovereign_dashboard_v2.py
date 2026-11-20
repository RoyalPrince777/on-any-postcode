"""Single SMI visual dashboard and canonical evidence still have distinct duties."""
from pathlib import Path

from mission_control import smi_73_signal_field

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "mission_control" / "templates" / "smi_visual_home.html"


def test_sovereign_dashboard_uses_canonical_mission_to_100_architecture():
    status = smi_73_signal_field.definition_status()
    assert status["signal_count"] == 73
    assert status["major_dimension_count"] == 21
    assert status["star_gate_count"] == 7
    assert status["reviewer_count"] == 14
    assert status["upgrade_only"] is True
    assert status["truth_mode"] is True


def test_sovereign_dashboard_front_surface_is_talk_first_and_no_fake_green():
    html = TEMPLATE.read_text(encoding="utf-8")
    for phrase in (
        "SOVEREIGN MEGAVERSE INTELLIGENCE",
        "SMI central command",
        "smi-talk-primary",
        "AUTO 3 / 7 / 21",
        "OAP systems",
        "GLOBAL INTELLIGENCE",
        "SYSTEM STATUS",
        "NOT CHECKED",
        "Founder Final",
    ):
        assert phrase in html
    assert "setInterval(" not in html
    assert ">Graphs<" not in html
    assert ">Monitors<" not in html


def test_sovereign_dashboard_preserves_one_front_door_and_deeper_systems():
    html = TEMPLATE.read_text(encoding="utf-8")
    for route in (
        "/mission/smi",
        "/mission/ollama",
        "/mission/war-room",
        "/mission/agents",
        "/movement",
        "/mission/brain",
        "/mission/smi/status",
    ):
        assert route in html
