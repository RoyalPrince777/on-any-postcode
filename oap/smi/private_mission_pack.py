"""Private SMI mission pack: bounded role projection over canonical Alliance.

No workers are started, no access is granted, and permanent family Packs remain
unchanged. Selection is a proposal, not evidence of runtime execution.
"""
from __future__ import annotations

from dataclasses import dataclass

from oap.smi.alliance_selection import select_alliance

PRIVATE_MISSION_ROLES: tuple[tuple[str, str], ...] = (
    ("Gyata", "founder_command"),
    ("Guardian", "permission_boundary"),
    ("Gorilla", "physical_last_line_defence"),
    ("Fox", "recovery_and_offline"),
    ("Neo", "engineering"),
    ("Architect", "architecture"),
    ("Keymaker", "routes"),
    ("Trinity", "multimodal_recognition"),
    ("Elephant", "canonical_memory"),
    ("Bagheera", "privacy"),
    ("Spider", "dependencies"),
    ("Octopus", "orchestration"),
    ("Owl", "legal_research"),
    ("Oracle", "evidence"),
    ("Seraph", "security_receipts"),
    ("Morpheus", "training"),
    ("Agent Smith", "adversarial_simulation"),
    ("Shere Khan", "failure_hunting"),
    ("Mouse", "edge_cases"),
)

@dataclass(frozen=True)
class PrivateMissionPack:
    roles: tuple[tuple[str, str], ...]
    canonical_specialists: tuple[str, ...]
    unassigned_capabilities: tuple[str, ...]
    queen_bee_assigned: bool
    advisory_only: bool = True
    runtime_verified: bool = False
    authority_granted: bool = False
    permanent_wolf_pack_unchanged: bool = True
    matrix_core_unchanged: bool = True


def private_smi_mission_pack(*, distributed_work: bool = False) -> PrivateMissionPack:
    """Project distinct responsibilities; never mutate canonical agent families."""
    selected = select_alliance(
        "TECHNICAL",
        "code architecture memory multimodal agent workflow local offline recovery evidence",
        distributed_work=distributed_work,
    )
    roles = PRIVATE_MISSION_ROLES
    if distributed_work:
        roles += (("Queen Bee", "distributed_worker_coordination"),)
    return PrivateMissionPack(
        roles=roles,
        canonical_specialists=selected.specialists,
        unassigned_capabilities=selected.unassigned_capabilities,
        queen_bee_assigned=distributed_work,
    )
