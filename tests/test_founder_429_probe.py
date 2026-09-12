from pathlib import Path


def test_founder_429_probe_is_anonymous_and_bounded():
    probe = Path("scripts/probe_founder_429.sh").read_text(encoding="utf-8")
    assert "/auth/recover-founder?next=/mission/ollama" in probe
    assert "/auth/founder-entry?next=/mission/ollama" in probe
    assert "--connect-timeout 10" in probe
    assert "--max-time 20" in probe
    assert "-X POST" not in probe
    assert "recovery_code=" not in probe
    assert "password=" not in probe
