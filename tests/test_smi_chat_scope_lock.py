from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_scope_lock_keeps_consequential_authority_unchanged():
    doc = (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").read_text()
    for phrase in ("Founder authentication", "passwords", "permissions", "database schema", "execution authority", "publishing authority", "payment authority"):
        assert phrase in doc
