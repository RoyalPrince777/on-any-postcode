from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_war_room_exposes_governed_four_step_recovery_controls():
    page = (ROOT / "mission_control" / "templates" / "war_room.html").read_text()

    assert 'data-proof="rollback-recovery"' in page
    assert 'data-proof="runtime-guard"' in page
    assert 'data-proof="isolation-recovery"' in page
    assert 'class="btn primary js-complete-green"' in page
    assert "/mission/smi-proof/" in page
    assert "['rollback-recovery', '25']" in page
    assert "['runtime-guard', '50']" in page
    assert "['isolation-recovery', '75']" in page
    assert "await runFounderFinal()" in page
    assert "production state unchanged" in page
    assert "Protocol stopped safely" in page
    assert "execution authority unchanged" in page
