"""Read-only Akela relationship view: family membership is not mission assignment.

This additive model grants no agent authority and makes no runtime activity claims.
"""
from __future__ import annotations

WOLF_PACK = (
    ("Akela", "Pack leader"),
    ("Raksha", "Protection and care"),
    ("Father Wolf", "Family stability and safeguarding"),
    ("Grey Brother", "Observation and reconnaissance"),
    ("Wolf Cubs", "Learning and development"),
    ("Wolf Pack", "Collective coordination"),
)

MISSION_ROLES = (
    ("Akela", "Pack selection"),
    ("Neo", "Engineering"),
    ("Spider", "Dependencies"),
    ("Octopus", "Coordination"),
    ("Bagheera", "Security"),
    ("Oracle", "Verification"),
    ("Fox", "Recovery"),
)


def akela_alliance_view() -> dict:
    """Detached projection. Assignments are proposals, not activity receipts."""
    return {
        "agent": "Akela",
        "family": "Jungle Book Intelligence / Wolf Pack",
        "wolf_pack": [
            {"name": name, "role": role, "relationship": "family"}
            for name, role in WOLF_PACK
        ],
        "mission_packs": [{
            "mission": "OAP Living Organism",
            "members": [
                {"name": name, "role": role, "relationship": "mission",
                 "activity": "ASSIGNED_UNVERIFIED"}
                for name, role in MISSION_ROLES
            ],
        }],
        "runtime_verified": False,
        "authority_granted": False,
    }


def validate_akela_view() -> dict:
    errors = []
    if len({name for name, _ in WOLF_PACK}) != len(WOLF_PACK):
        errors.append("Duplicate wolf family member")
    if len({name for name, _ in MISSION_ROLES}) != len(MISSION_ROLES):
        errors.append("Duplicate mission role identity")
    view = akela_alliance_view()
    if any(member["relationship"] != "family" for member in view["wolf_pack"]):
        errors.append("Wolf Pack membership boundary changed")
    if any(member["relationship"] != "mission"
           for member in view["mission_packs"][0]["members"]):
        errors.append("Mission assignment boundary changed")
    return {"passed": not errors, "errors": errors}
