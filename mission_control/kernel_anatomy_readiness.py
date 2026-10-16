"""Read-only, fail-closed anatomy readiness projection for the Living Kernel.

A registered organ is not automatically a healthy organ. This module never
executes actions, changes permissions, or writes to the runtime database.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .organism import ORGANISM_SYSTEMS, validate_architecture


def anatomy_readiness(observations: Mapping[str, Mapping[str, Any]] | None = None) -> dict[str, Any]:
    """Project observed health onto canonical organs; absent evidence is UNKNOWN.

    An observation is valid only when it contains a timestamp, source and
    explicit healthy boolean. Caller owns freshness validation; until that
    validation is implemented, even healthy reports remain UNVERIFIED.
    """
    architecture = validate_architecture()
    supplied = observations or {}
    registered = {str(system["id"]) for system in ORGANISM_SYSTEMS}
    organs = []
    for system in ORGANISM_SYSTEMS:
        organ_id = str(system["id"])
        observation = supplied.get(organ_id)
        evidence_present = (
            isinstance(observation, Mapping)
            and isinstance(observation.get("source"), str)
            and bool(observation["source"].strip())
            and isinstance(observation.get("timestamp"), str)
            and bool(observation["timestamp"].strip())
            and type(observation.get("healthy")) is bool
        )
        organs.append({
            "id": organ_id,
            "name": system["name"],
            "anatomy": system["anatomy"],
            "status": "UNVERIFIED" if evidence_present else "UNKNOWN",
            "evidence_present": bool(evidence_present),
        })
    return {
        "architecture_valid": architecture["passed"],
        "ready": False,  # Evidence freshness and runtime linkage are not yet proven.
        "consequential_execution": False,
        "unknown_observations": sorted(set(supplied) - registered),
        "organs": organs,
    }
