"""Canonical read-only SMI Archive / History projection.

Archive is the organised knowledge view for SMI identity, anatomy, council,
governance, history, War Room, Mission-to-100, Digital SoC, evidence and
lessons. History is the chronological lineage inside Archive, not a second
memory engine, brain, registry or execution path.
"""
from __future__ import annotations

from typing import Any

from . import oap_inference_gateway

SMI_LINEAGE: tuple[dict[str, str], ...] = (
    {
        "name": "Synthetic Mind Intelligence",
        "position": "cognitive_origin",
        "meaning": "Thinking, perception, memory and reasoning lineage.",
    },
    {
        "name": "Sovereign Megaverse Intelligence",
        "position": "architectural_expansion",
        "meaning": "OAP-wide first-party coordination and sovereign control lineage.",
    },
    {
        "name": "Synthetic Machine Intelligence",
        "position": "canonical_current",
        "meaning": "Current technical definition of the single OAP machine-intelligence brain.",
    },
)

ARCHIVE_SECTIONS: tuple[dict[str, str], ...] = (
    {"id": "identity-lineage", "name": "Identity & Lineage", "purpose": "SMI names, meanings and evolution."},
    {"id": "anatomy", "name": "Anatomy", "purpose": "Brain, memory, interconnect, protection, execution and recovery."},
    {"id": "council", "name": "Council", "purpose": "Distinct advisory/review roles; no duplicate authority."},
    {"id": "laws-governance", "name": "Laws & Governance", "purpose": "Truth Mode, AEGIS, Green Gate and Human Authority boundaries."},
    {"id": "history", "name": "History", "purpose": "Chronological evolution, supersession and provenance."},
    {"id": "war-room", "name": "War Room", "purpose": "Red Team, Claw Test, checks, evidence and dissent."},
    {"id": "mission-to-100", "name": "Mission-to-100", "purpose": "Evidence-backed completion without cosmetic progress."},
    {"id": "sovereign-digital-soc", "name": "Sovereign Digital SoC", "purpose": "SMI as the single brain inside the software-defined organism."},
    {"id": "runtime-evidence", "name": "Runtime Evidence", "purpose": "Code, tests, deployment, health, recovery and proof."},
    {"id": "lessons-evolution", "name": "Lessons / Evolution", "purpose": "What changed, merged, failed, improved and why."},
)

COUNCIL_ROLES: tuple[dict[str, str], ...] = (
    {"name": "SMI Core", "role": "Internal synthesis", "boundary": "Single first-party brain; recommendation only."},
    {"name": "Neo", "role": "True path / recovery witness", "boundary": "Advisory; cannot approve or execute."},
    {"name": "Bagheera", "role": "Judgement / restraint", "boundary": "Present at the beginning and end of major reviews."},
    {"name": "Shere Khan", "role": "Adversarial Stress-Test / Threat Intelligence / Failure-Hunter", "boundary": "Claw Test asks: What can break this?"},
    {"name": "Agent Smith", "role": "Duplicate / inconsistency / replication hunter", "boundary": "Distinct from Shere Khan survivability testing."},
    {"name": "Twinz", "role": "Dual-path contradiction / alternate-route review", "boundary": "Advisory consistency check."},
    {"name": "ALL IN A.I.", "role": "Always Involved · Captain Agent · Mission Keeper", "boundary": "External assistant/operator; not first-party authority."},
    {"name": "Founder Final", "role": "Human Authority", "boundary": "Final consequential authority remains human."},
)

SHERE_KHAN_CLAW_TEST: tuple[dict[str, str], ...] = (
    {"area": "survivability", "question": "Does useful service remain after partial failure?"},
    {"area": "dependency_risk", "question": "Can one hidden dependency take down the system?"},
    {"area": "authority_risk", "question": "Can any role bypass Guardian, AEGIS or Human Authority?"},
    {"area": "failure_propagation", "question": "Can one failed organ contaminate others?"},
    {"area": "recovery", "question": "Can a known-good state be restored and verified?"},
    {"area": "evidence", "question": "Is the claim supported by test or runtime evidence?"},
    {"area": "false_confidence", "question": "Is Green being claimed because it sounds complete rather than being proven?"},
)

CORE_LAW: tuple[str, ...] = (
    "History is preserved.",
    "Duplicates are merged.",
    "Roles stay distinct.",
    "Evidence beats confidence.",
    "Shere Khan attacks before Green.",
    "Bagheera judges before Green.",
    "ALL IN stays involved as an external review role.",
    "Founder Final remains final.",
)

MISSION_TO_100_PROTOCOL: tuple[dict[str, str], ...] = (
    {
        "id": "direct-work",
        "rule": "Do the smallest real work that closes the measured gap; do not add stages, demos or duplicate reports.",
    },
    {
        "id": "exact-artifact-parity",
        "rule": "The artifact tested and approved must match the artifact bound to the target runtime before production Green.",
    },
    {
        "id": "target-runtime-proof",
        "rule": "A passing branch, build or sibling service cannot prove the target service; target health and binding must be read back.",
    },
    {
        "id": "no-average-away",
        "rule": "A failed or unknown mandatory final gate cannot be averaged into 100 by strong scores elsewhere.",
    },
    {
        "id": "dissent-survives",
        "rule": "Material dissent, Claw Test findings and unresolved evidence remain visible until resolved or explicitly held by Human Authority.",
    },
    {
        "id": "rollback-before-promotion",
        "rule": "A known-good recovery path must exist before replacing a proven runtime artifact.",
    },
    {
        "id": "founder-final",
        "rule": "Green Gate evidence informs the decision; Founder Final remains the consequential human authority.",
    },
)


def status() -> dict[str, Any]:
    """Return the canonical archive projection without creating new authority."""

    current = next(item for item in SMI_LINEAGE if item["position"] == "canonical_current")
    inference = oap_inference_gateway.status(probe=False)
    bridge = dict(inference.get("home_node_bridge") or {})
    return {
        "component": "SMI Archive",
        "ready": True,
        "mode": "read_only_organised_projection",
        "current_name": current["name"],
        "lineage": tuple(dict(item) for item in SMI_LINEAGE),
        "sections": tuple(dict(item) for item in ARCHIVE_SECTIONS),
        "council": tuple(dict(item) for item in COUNCIL_ROLES),
        "shere_khan": {
            "canonical_role": "Adversarial Stress-Test / Threat Intelligence / Failure-Hunter",
            "mode": "The Claw Test",
            "opening_question": "What can break this?",
            "checks": tuple(dict(item) for item in SHERE_KHAN_CLAW_TEST),
            "beginning_and_end_review_presence": True,
        },
        "core_law": CORE_LAW,
        "mission_to_100_protocol": tuple(dict(item) for item in MISSION_TO_100_PROTOCOL),
        "exact_artifact_parity_required_for_production_green": True,
        "mandatory_gate_can_be_averaged_away": False,
        "runtime_evidence": {
            "first_party_inference": {
                "ready": bool(inference.get("first_party_inference_ready")),
                "local_enabled": bool(inference.get("local_enabled")),
                "local_url_configured": bool(inference.get("local_url_configured")),
                "local_model_configured": bool(inference.get("local_model_configured")),
                "bridge_configured": bool(bridge.get("configured")),
                "worker_recently_seen": bool(bridge.get("worker_recently_seen")),
                "durable_worker_fresh": bool(bridge.get("durable_worker_fresh")),
                "worker_ready": bool(bridge.get("worker_ready")),
                "transport": bridge.get("transport"),
                "proof_rule": "Green requires a real recent Home Node worker or a verified local model runtime; configuration alone is not proof.",
            }
        },
        "history_is_timeline_inside_archive": True,
        "new_brain_created": False,
        "new_memory_engine_created": False,
        "new_execution_authority_created": False,
        "human_authority_final": True,
    }
