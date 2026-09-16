from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_completion_record_names_canonical_layers():
    text = (ROOT / "docs/SMI_CHAT_PRODUCT_COMPLETION.md").read_text()
    for phrase in (
        "SMI Chat is the private Founder front door",
        "SMI AUTO is the visible orchestration mode",
        "OAP Studio Intelligence remains the canonical media intelligence engine",
        "HRM/JOOG remains the continuity and audited-memory layer",
        "War Room remains the governed research, challenge and review layer",
        "Guardian and Human Authority remain unchanged",
    ):
        assert phrase in text
