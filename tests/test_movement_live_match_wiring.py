from __future__ import annotations

from pathlib import Path


def test_live_movement_match_routes_use_hardened_store():
    source = Path("mission_control/movement_routes.py").read_text(encoding="utf-8")

    assert "movement_match_safety," in source
    assert "movement_match_safety.STORE.propose_match(" in source
    assert "movement_match_safety.STORE.accept_match(" in source
    assert "movement_operations.STORE.propose_match(" not in source
    assert "movement_operations.STORE.accept_match(" not in source
