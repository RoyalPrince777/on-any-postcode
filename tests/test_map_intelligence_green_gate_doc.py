from pathlib import Path


def test_green_gate_requires_ci_and_live_proof():
    text = Path("docs/OAP_MAP_INTELLIGENCE_GREEN_GATE.md").read_text(encoding="utf-8").casefold()
    assert "ci success" in text
    assert "approved deployment" in text
    assert "live verification" in text
