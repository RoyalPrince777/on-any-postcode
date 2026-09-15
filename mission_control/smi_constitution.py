"""Canonical SMI 21-law constitution and governed organism anatomy.

This module is declarative by design: it defines authority and review boundaries
without granting execution capability. Human Authority remains final.
"""

from __future__ import annotations

from typing import Final

SMI_HIERARCHY: Final[tuple[str, ...]] = (
    "Human Authority",
    "SMI",
    "Living Kernel",
    "Nexus",
    "Specialist Intelligence",
)

SMI_ANATOMY: Final[dict[str, str]] = {
    "Human Authority": "Final sovereign authority for consequential real-world action.",
    "SMI": "Highest intelligence; classifies risk and coordinates governed reasoning.",
    "Living Kernel": "Subordinate runtime/orchestration heartbeat; cannot grant authority.",
    "Nexus": "Connection and evidence-routing fabric; does not judge truth.",
    "Octopus": "Systems Intelligence specialist; diagnoses dependencies and recommends recovery.",
    "Signal Intelligence Monitor": "Senses and reports evidence; has no execution authority.",
    "Judgement": "Challenges evidence, uncertainty, consequences and reversibility.",
    "Guardian": "Protection layer; may pass, require review, or block.",
    "HRM": "Governed memory, audit and receipts; memory cannot authorize action.",
    "Oasis": "Isolated learning/simulation environment; cannot promote itself to production.",
    "Matrix System": "Environment containing registered Matrix Intelligence agents; not an agent.",
    "War Room": "SMI command and evidence surface; not a separate brain or authority.",
}

MIND_LAWS: Final[tuple[str, ...]] = (
    "Proof before execution",
    "Verification before sharing",
    "Evidence before certainty",
    "Context before judgement",
    "Uncertainty must be declared",
    "Counter-cases must be tested",
    "Learning must improve future reasoning",
)

BODY_LAWS: Final[tuple[str, ...]] = (
    "Compliance before public claims",
    "Ownership before dependency",
    "Audit before automation",
    "Stability before expansion",
    "Minimum necessary access",
    "Fail closed when authority or identity is uncertain",
    "Every consequential action must be traceable and reversible where possible",
)

SOUL_LAWS: Final[tuple[str, ...]] = (
    "Community before middlemen",
    "Human approval before real-world action",
    "Human Authority remains final",
    "Agent cooperation never transfers authority",
    "Guardian protection overrides speed",
    "Youth and vulnerable-user protection comes before engagement",
    "No agent may rewrite the constitution, elevate its own authority, or bypass 3→7→21 governance",
)

TWENTY_ONE_LAWS: Final[tuple[str, ...]] = MIND_LAWS + BODY_LAWS + SOUL_LAWS
REVIEW_DEPTHS: Final[tuple[int, ...]] = (3, 7, 21)

WAR_ROOM_CYCLE: Final[tuple[str, ...]] = (
    "Signal Intelligence Monitor",
    "Nexus",
    "Octopus",
    "Living Kernel",
    "SMI",
    "Judgement",
    "Guardian",
    "Human Authority",
    "Execution",
    "HRM",
    "Oasis",
)


def review_depth(*, consequential: bool = False, critical: bool = False) -> int:
    """Return the minimum governed review depth; risk may force 21 immediately."""
    if critical:
        return 21
    if consequential:
        return 7
    return 3


def constitution_status() -> dict[str, object]:
    """Return bounded, non-secret constitutional metadata for War Room/status UI."""
    return {
        "highest_intelligence": "SMI",
        "final_authority": "Human Authority",
        "living_kernel_subordinate": True,
        "war_room_is_command_surface": True,
        "law_count": len(TWENTY_ONE_LAWS),
        "review_depths": list(REVIEW_DEPTHS),
        "authority_transfer_by_agent_cooperation": False,
        "oasis_auto_promote": False,
    }
