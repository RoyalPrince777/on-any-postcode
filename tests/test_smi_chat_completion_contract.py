from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text()


def test_smi_chat_completion_keeps_one_canonical_control_owner():
    controller = read("mission_control/static/smi_canonical_controller.js")
    assert "singleSubmitOwner:true" in controller
    assert "micOwner:true" in controller
    assert "voiceOwner:true" in controller
    assert "stopOwner:true" in controller
    assert "cameraCapture:true" in controller
    assert "screenCapture:true" in controller
    assert "studioDuplicate:false" in controller


def test_smi_chat_completion_keeps_governed_intelligence_endpoints():
    wrapper = read("mission_control/templates/ollama_chat.html")
    for contract in (
        "workbenchUrl", "healthUrl", "streamUrl", "warRoomUrl",
        "functionHealthUrl", "routesUrl", "greenGateUrl", "signalsUrl",
        "guardianUrl", "hrmUrl", "improvementUrl",
    ):
        assert contract in wrapper


def test_smi_chat_completion_does_not_touch_auth_contract():
    identity = read("mission_control/static/smi_product_identity.js")
    assert "password" not in identity.lower()
    assert "auth" not in identity.lower()
    assert "permission" not in identity.lower()
