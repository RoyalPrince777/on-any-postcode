from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_identity_is_oap_native_not_provider_branded():
    identity = (ROOT / "mission_control/static/smi_product_identity.js").read_text()
    for provider in ("ChatGPT", "Claude", "Gemini", "Grok", "Kimi"):
        assert provider not in identity
    assert "Sovereign Megaverse Intelligence" in identity
