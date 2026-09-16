from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_completion_manifest_covers_product_gate_without_claiming_runtime_proof():
    gate = (ROOT / "tests/test_smi_chat_product_gate.py").read_text()
    doc = (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").read_text()
    expected = (
        "single_smi", "auto", "chat", "history", "files", "images", "voice",
        "camera", "screen", "stop", "mobile", "war_room", "signals", "guardian",
        "hrm", "function_health", "green_gate", "no_studio_duplicate",
    )
    for item in expected:
        assert f'"{item}"' in gate
    assert "live handset proof" in doc
