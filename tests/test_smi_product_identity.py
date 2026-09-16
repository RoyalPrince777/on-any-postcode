from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_smi_wrapper_loads_product_identity_after_base_ui():
    text = (ROOT / "mission_control/templates/ollama_chat.html").read_text()
    assert "smi_product_identity.js" in text
    assert text.index("ollama_chat_base.html") < text.index("smi_product_identity.js")


def test_product_identity_consolidates_visible_oap_mind_copy_without_new_engine():
    text = (ROOT / "mission_control/static/smi_product_identity.js").read_text()
    assert "Sovereign Megaverse Intelligence" in text
    assert "Message SMI" in text
    assert "SMI AUTO" in text
    assert "OAP Mind" in text
    assert "fetch(" not in text
    assert "XMLHttpRequest" not in text


def test_product_identity_preserves_canonical_controller_and_studio_boundary():
    wrapper = (ROOT / "mission_control/templates/ollama_chat.html").read_text()
    controller = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text()
    assert "smi_canonical_controller.js" in wrapper
    assert "studioDuplicate:false" in controller
    assert "singleSubmitOwner:true" in controller
