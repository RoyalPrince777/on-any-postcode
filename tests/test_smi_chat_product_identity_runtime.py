from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_identity_runtime_changes_labels_without_replacing_controls():
    text = (ROOT / "mission_control/static/smi_product_identity.js").read_text()
    assert "document.title" in text
    assert "querySelector('.chat-title')" in text
    assert "getElementById('message')" in text
    assert "getElementById('provider-state')" in text
    assert "getElementById('send')" not in text
    assert "getElementById('chat-form')" not in text
