from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_smi_chat_has_mobile_single_column_workspace():
    base = (ROOT / "mission_control/templates/ollama_chat_base.html").read_text()
    assert "@media(max-width:820px)" in base
    assert ".workspace-grid{grid-template-columns:1fr" in base
    assert ".history{display:none}" in base
    assert ".composer{padding:8px}" in base


def test_smi_chat_uses_dynamic_viewport_height():
    base = (ROOT / "mission_control/templates/ollama_chat_base.html").read_text()
    assert "height:100dvh" in base
