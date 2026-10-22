from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_oap_home_signing_setup_is_local_private_and_pinned():
    source = (ROOT / "scripts" / "oap_home_signing_setup.sh").read_text(encoding="utf-8")

    assert 'KEY_DIR="${HOME}/oap-private"' in source
    assert 'KEYSTORE="${KEY_DIR}/oap-home-v2.jks"' in source
    assert 'ALIAS="oap-home-v2"' in source
    assert "refusing_to_overwrite_existing_oap_home_identity" in source
    assert "-storetype PKCS12" in source
    assert "-keysize 4096" in source
    assert "certificate_sha256=" in source
    assert "OAP_HOME_KEYSTORE_B64" in source
    assert "OAP_HOME_CERT_SHA256" in source
    assert "PRIVATE_KEY_NOT_COMMITTED" in source
    assert "git add" not in source
    assert "git push" not in source
