from pathlib import Path
import re

BLUEPRINT = Path("docs/OAP_FULL_MASTER_BLUEPRINT_DASHBOARD_CHAT.md")


def test_master_blueprint_has_exactly_101_capabilities_not_stages():
    source = BLUEPRINT.read_text(encoding="utf-8")
    entries = re.findall(r"^B101-(\\d{3}) · ", source, flags=re.MULTILINE)
    assert entries == [f"{index:03d}" for index in range(1, 102)]
    assert "101 capabilities ≠ 101 stages." in source
    assert "Human Authority remains final." in source


def test_master_blueprint_101_preserves_truth_states_and_hard_boundaries():
    source = BLUEPRINT.read_text(encoding="utf-8")
    for state in ("BUILT", "BOUNDED", "GATED"):
        assert state in source
    for boundary in (
        "No self-permission expansion",
        "Consequential-action execution lock",
        "Regulated money movement / issuance",
        "A7 certified organism-scale autonomy",
    ):
        assert boundary in source
