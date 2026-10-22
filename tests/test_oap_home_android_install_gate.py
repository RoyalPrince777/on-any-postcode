from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_oap_home_android_install_gate_is_non_destructive():
    source = (ROOT / "scripts" / "oap_home_android_install_gate.sh").read_text(encoding="utf-8")

    assert 'V2="com.onanypostcode.oaphome.v2"' in source
    assert 'V1="com.onanypostcode.oaphome"' in source
    assert 'pm path "${V2}"' in source
    assert 'pm path "${V1}"' in source
    assert 'REQUEST_INSTALL_PACKAGES' in source
    assert 'RESULT=EXISTING_V2_PRESENT' in source
    assert 'RESULT=NO_EXISTING_V2' in source
    assert 'MANAGE_UNKNOWN_APP_SOURCES' in source
    assert 'pm uninstall' not in source
    assert 'adb uninstall' not in source
    assert 'rm -rf /data/app' not in source
