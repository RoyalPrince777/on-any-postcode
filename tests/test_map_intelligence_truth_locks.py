from mission_control.map_intelligence import TRUTH_LOCKS


def test_consequential_map_intelligence_actions_stay_locked():
    locks = set(TRUTH_LOCKS)
    assert {"turn-by-turn routing", "confirmed supplier booking", "payment", "automatic dispatch", "live tracking"}.issubset(locks)
