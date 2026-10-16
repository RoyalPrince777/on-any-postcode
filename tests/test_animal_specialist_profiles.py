"""Regression tests for named animal specialist profiles."""
from mission_control import agents
from mission_control.animal_specialist_profiles import PROFILES, get_profile, validate_profiles


def test_profiles_are_distinct_and_fail_closed():
    assert validate_profiles()
    assert set(PROFILES) == {"leo", "naughty", "natue"}
    assert get_profile("LEO")["animal"] == "Cat"
    assert get_profile("Naughty")["animal"] == "Rottweiler"
    assert get_profile("Natue")["animal"] == "Pitbull"
    assert all(not p["execution_enabled"] for p in PROFILES.values())
    assert all(not p["registry_member"] for p in PROFILES.values())


def test_locked_registry_unchanged():
    assert agents.LOCKED_AGENT_COUNT == 78
    assert len(agents.AGENT_REGISTRY) == 78
    assert sum(a["family_id"] == "animal" for a in agents.AGENT_REGISTRY) == 21
    assert all(p["name"] not in {a["name"] for a in agents.AGENT_REGISTRY} for p in PROFILES.values())
