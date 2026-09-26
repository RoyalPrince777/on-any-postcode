from pathlib import Path

INIT = Path("mission_control/__init__.py")


def test_lab_recovery_failure_blocks_lab_not_public_app_startup():
    text = INIT.read_text(encoding="utf-8")
    assert '"event": "oap_lab_recovery_gate"' in text
    assert '"lab_release_blocked": True' in text
    assert '"public_app_startup_blocked": False' in text
    assert 'raise RuntimeError("oap_lab_recovery_live_proof_failed")' not in text
