from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_identity_layer_loads_before_interaction_controllers():
    text = (ROOT / "mission_control/templates/ollama_chat.html").read_text()
    identity = text.index("smi_product_identity.js")
    final_ui = text.index("smi_chat_final.js")
    canonical = text.index("smi_canonical_controller.js")
    assert identity < final_ui < canonical
