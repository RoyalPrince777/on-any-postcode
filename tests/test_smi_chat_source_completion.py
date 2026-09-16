from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_source_completion_slice_is_coherent():
    required = (
        "mission_control/templates/ollama_chat.html",
        "mission_control/static/smi_product_identity.js",
        "mission_control/static/smi_canonical_controller.js",
        "docs/SMI_CHAT_PRODUCT_COMPLETION.md",
    )
    for path in required:
        assert (ROOT / path).exists()
