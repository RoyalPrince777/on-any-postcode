from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_governed_ci_trigger_has_completion_artifacts():
    assert (ROOT / "mission_control/static/smi_product_identity.js").is_file()
    assert (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").is_file()
