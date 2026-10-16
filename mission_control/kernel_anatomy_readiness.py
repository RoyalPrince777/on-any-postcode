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


def runtime_anatomy_snapshot() -> dict[str, Any]:
    """Read existing runtime evidence without claiming whole-organism readiness.

    The timestamp describes when the observation was collected, not when the
    worker heartbeat occurred. Runtime freshness remains runtime_status's job.
    """
    from datetime import datetime, timezone

    from .organism_runtime import runtime_status

    try:
        status = runtime_status()
        if not isinstance(status, Mapping):
            raise TypeError("runtime status must be a mapping")
    except Exception:  # noqa: BLE001 - a failed probe must not imply readiness.
        status = {
            "ready": False,
            "schema_ready": False,
            "worker_fresh": False,
            "error": "runtime_probe_unavailable",
        }
    observed_at = datetime.now(timezone.utc).isoformat()
    heart = {
        "healthy": bool(status.get("ready") is True),
        "source": "organism_runtime.runtime_status",
        "timestamp": observed_at,
    }
    projection = anatomy_readiness({"living_kernel": heart})
    projection["runtime"] = {
        "ready": status.get("ready") is True,
        "schema_ready": status.get("schema_ready") is True,
        "worker_fresh": status.get("worker_fresh") is True,
        "error": status.get("error"),
        "observed_at": observed_at,
    }
    return projection


MASTER_VITALS = (
    "Pulse", "Awareness", "Circulation", "Integrity", "Continuity",
    "Energy", "Balance", "Adaptation", "Participation", "Purpose",
)


def master_vitals_snapshot() -> dict[str, Any]:
    """Expose ten named vitals without inventing measurements.

    Pulse is backed by the existing runtime readiness check, but stays
    UNVERIFIED at the whole-organism level. Other vitals remain UNKNOWN
    until independently measured by their responsible subsystems.
    """
    anatomy = runtime_anatomy_snapshot()
    runtime = anatomy["runtime"]
    vitals = []
    for name in MASTER_VITALS:
        if name == "Pulse":
            status = "UNVERIFIED" if runtime["ready"] else "DEGRADED"
            source = "organism_runtime.runtime_status"
        else:
            status = "UNKNOWN"
            source = None
        vitals.append({"name": name, "status": status, "source": source})
    return {
        "ready": False,
        "consequential_execution": False,
        "vitals": vitals,
        "anatomy": anatomy,
    }
