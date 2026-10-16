"""Named, non-executing Animal Intelligence specialist profiles.

These are governed profiles, NOT additional registered agents. Their presence
must not change the canonical 78-agent roster or the 21 animal archetypes.
"""
from __future__ import annotations

from types import MappingProxyType

_ALLOWED = frozenset({"READ", "ANALYSE", "RECOMMEND"})
_PROFILES = {
    "leo": {
        "name": "Leo",
        "animal": "Cat",
        "family_id": "animal",
        "world_id": "life",
        "role": "Anomaly Observation Specialist",
        "capabilities": ("anomaly_observation", "signal_triage", "precision_review"),
        "collaborators": ("Owl", "Falcon", "Panther"),
    },
    "naughty": {
        "name": "Naughty",
        "animal": "Rottweiler",
        "family_id": "animal",
        "world_id": "life",
        "role": "Security Boundary Review Specialist",
        "capabilities": ("boundary_review", "access_anomaly_triage", "guardian_escalation"),
        "collaborators": ("Bagheera", "Seraph"),
    },
    "natue": {
        "name": "Natue",
        "animal": "Pitbull",
        "family_id": "animal",
        "world_id": "life",
        "role": "Recovery Evidence Specialist",
        "capabilities": ("failure_analysis", "recovery_review", "regression_evidence"),
        "collaborators": ("Gorilla", "Tank", "Dozer"),
    },
}

PROFILES = MappingProxyType({
    key: MappingProxyType({
        **value,
        "permissions": tuple(sorted(_ALLOWED)),
        "execution_enabled": False,
        "approval_authority": False,
        "final_authority": "Founder",
        "guardian_gate_required": True,
        "audit_required": True,
        "registry_member": False,
    })
    for key, value in _PROFILES.items()
})


def get_profile(name: str):
    """Read-only lookup; no autonomous action or runtime routing."""
    return PROFILES[name.casefold()]


def validate_profiles() -> bool:
    assert len(PROFILES) == 3
    assert len({v["name"].casefold() for v in PROFILES.values()}) == 3
    for profile in PROFILES.values():
        assert profile["family_id"] == "animal"
        assert profile["world_id"] == "life"
        assert set(profile["permissions"]) <= _ALLOWED
        assert not profile["execution_enabled"]
        assert not profile["approval_authority"]
        assert not profile["registry_member"]
        assert profile["guardian_gate_required"] and profile["audit_required"]
    return True
