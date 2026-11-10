"""KORADASO noise mission stays inside the existing side-effect-free SMI router."""
from mission_control import smi_auto


def test_koradaso_noise_route_is_governed_and_not_auto_executed():
    routed = smi_auto.observe(
        "GET", "/koradaso", message="SMI strip noise and restore UI"
    )
    mission = routed["koradaso_noise_mission"]
    assert mission["mission"] == "koradaso_ui_noise_recovery"
    assert mission["existing_pr"] == 1388
    assert mission["owner"] == "SMI"
    assert mission["observe_only"] is True
    assert mission["automatic_github_edits_enabled"] is False
    assert mission["execution_granted"] is False
    assert mission["human_authority_final"] is True
    assert {"ux", "verification", "resilience"}.issubset(routed["lenses"])


def test_unrelated_requests_do_not_trigger_koradaso_mission():
    assert smi_auto.observe("GET", "/world", message="search")["koradaso_noise_mission"] is None
    assert smi_auto.observe("GET", "/koradaso", message="view home")["koradaso_noise_mission"] is None


def test_named_koradaso_mission_routes_from_smi_command():
    result = smi_auto.observe("GET", "/mission", message="KORADASO auto fix noise")
    assert result["koradaso_noise_mission"]["guardian_required"] is True
    assert result["koradaso_noise_mission"]["green_gate_required"] is True
