"""Read-only 13-dimension OAP Living Organism registry.

An additive classification, not an agent anatomy replacement, runtime worker,
authority grant, or a new set of Master Vitals.
"""
from __future__ import annotations

from types import MappingProxyType

DIMENSION_NAMES = (
    "Mind", "Body", "Soul", "Spirit", "Heart", "Senses", "Conscience",
    "Identity", "Memory", "Will", "Time", "Growth", "Recovery",
)
MASTER_VITAL_NAMES = (
    "Pulse", "Awareness", "Circulation", "Integrity", "Continuity",
    "Energy", "Balance", "Adaptation", "Participation", "Purpose",
)
# Explicitly non-executing architectural responsibility labels.
_DIMENSION_ROLES = {
    "Mind": ("SMI", "Morpheus", "Owl"),
    "Body": ("Neo", "Octopus", "Tigress"),
    "Soul": ("Gyata", "Mowgli", "Lioness"),
    "Spirit": ("Akela", "Panther", "Fox"),
    "Heart": ("Raksha", "Lioness", "Guardian"),
    "Senses": ("Eagle", "Falcon", "Grey Brother"),
    "Conscience": ("Bagheera", "Seraph", "Owl"),
    "Identity": ("Architect", "Keymaker", "Bagheera"),
    "Memory": ("Elephant", "Colonel Hathi", "HRM"),
    "Will": ("Gyata", "Akela", "Captain ALL IN"),
    "Time": ("Architect", "Oracle"),
    "Growth": ("MANSA", "Neo", "Baloo"),
    "Recovery": ("Fox", "Twins", "Gorilla"),
}
DIMENSION_ROLES = MappingProxyType(_DIMENSION_ROLES)


def validate_dimensions() -> dict:
    errors = []
    if len(DIMENSION_NAMES) != 13 or len(set(DIMENSION_NAMES)) != 13:
        errors.append("Exactly 13 unique dimensions required")
    if set(DIMENSION_NAMES) != set(DIMENSION_ROLES):
        errors.append("Every dimension requires exactly one role mapping")
    if len(MASTER_VITAL_NAMES) != 10 or len(set(MASTER_VITAL_NAMES)) != 10:
        errors.append("The ten Master Vitals must remain distinct")
    if any(not roles or len(set(roles)) != len(roles) for roles in DIMENSION_ROLES.values()):
        errors.append("Dimension roles must be nonempty and unique within a dimension")
    return {"passed": not errors, "errors": errors}


def get_dimension_registry() -> dict:
    """Return a detached, serialisable projection; never grants execution authority."""
    return {
        "dimensions": [
            {"name": name, "advisory_roles": list(DIMENSION_ROLES[name])}
            for name in DIMENSION_NAMES
        ],
        "master_vitals": list(MASTER_VITAL_NAMES),
        "authority": "Human Authority",
        "execution_enabled": False,
        "validation": validate_dimensions(),
    }
