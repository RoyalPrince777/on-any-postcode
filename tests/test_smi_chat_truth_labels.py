from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_product_completion_doc_requires_live_device_proof():
    text = (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").read_text()
    assert "live handset proof" in text
    assert "Microphone, camera and screen permissions" in text
    assert "continuous live screen/video understanding" in text


def test_scope_lock_explicitly_excludes_auth_and_authority_changes():
    text = (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").read_text()
    assert "does not change Founder authentication" in text
    assert "execution authority" in text
    assert "publishing authority" in text
    assert "payment authority" in text
