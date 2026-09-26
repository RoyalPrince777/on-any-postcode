"""Owner-scoped, non-consequential Studio workspace orchestration.

This module plans and checkpoints multi-workspace Studio missions. It never grants
execution, deployment, database-write, publishing, distribution or payment authority.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from . import studio_intelligence, workspaces

_ORDER = ("research", "data", "build", "code", "motion", "music", "omni")
_DEPENDENCIES: dict[str, tuple[str, ...]] = {
    "research": (),
    "data": ("research",),
    "build": ("research", "data"),
    "code": ("build",),
    "motion": ("research",),
    "music": ("research",),
    "omni": ("research",),
}
_TERMS: dict[str, tuple[str, ...]] = {
    "research": ("research", "source", "evidence", "compare", "latest"),
    "data": ("database", "schema", "data", "table", "query", "migration"),
    "build": ("build", "app", "website", "dashboard", "product", "preview"),
    "code": ("code", "debug", "test", "refactor", "commit", "pull request"),
    "motion": ("video", "motion", "animate", "scene", "camera"),
    "music": ("music", "song", "beat", "lyrics", "mix", "master"),
    "omni": ("screen", "camera", "document", "image", "audio", "multimodal"),
}


def _digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def _selected(prompt: object) -> tuple[str, ...]:
    text = str(prompt or "").casefold()
    hits = {wid for wid, terms in _TERMS.items() if any(term in text for term in terms)}
    if not hits:
        chosen = studio_intelligence.select_workspace(text)["id"]
        if chosen != "auto":
            hits.add(chosen)
    expanded = set(hits)
    for wid in tuple(hits):
        expanded.update(_DEPENDENCIES.get(wid, ()))
    return tuple(wid for wid in _ORDER if wid in expanded)


def plan(prompt: object, *, mission_id: object | None = None) -> dict[str, Any]:
    text = str(prompt or "").strip()
    if not text:
        raise ValueError("orchestration_prompt_required")
    mission = str(uuid.UUID(str(mission_id))) if mission_id else str(uuid.uuid4())
    selected = _selected(text)
    if not selected:
        selected = ("research",)
    steps = []
    for index, wid in enumerate(selected, 1):
        profile = studio_intelligence.workspace(wid)
        deps = tuple(dep for dep in _DEPENDENCIES.get(wid, ()) if dep in selected)
        steps.append(
            {
                "step": index,
                "workspace": wid,
                "name": profile["name"],
                "depends_on": deps,
                "state": "queued",
                "execution_authorised": False,
                "human_authority_required_for_consequential_action": True,
            }
        )
    payload = {
        "mission_id": mission,
        "prompt_summary": text[:280],
        "steps": steps,
        "workspace_count": len(steps),
        "checkpoint_every": 3,
        "max_steps": 21,
        "resumable": True,
        "execution_authorised": False,
        "deploy_authorised": False,
        "database_write_authorised": False,
        "publish_authorised": False,
        "distribution_authorised": False,
        "payment_authorised": False,
        "human_authority_final": True,
    }
    return {**payload, "digest": _digest(payload)}


def _history(owner_id: object, mission_id: object) -> list[dict[str, Any]]:
    mission = str(uuid.UUID(str(mission_id)))
    rows = workspaces.list_studio_orchestration_records(owner_id, mission, limit=100)
    if len(rows) >= 100:
        raise RuntimeError("orchestration_history_limit_reached")
    versions: list[dict[str, Any]] = []
    previous = "GENESIS"
    for index, row in enumerate(rows, 1):
        try:
            entry = json.loads(row["body"])
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError("orchestration_history_unreadable") from exc
        if not isinstance(entry, dict):
            raise TypeError("orchestration_history_invalid")
        payload = {key: value for key, value in entry.items() if key != "digest"}
        if (
            entry.get("mission_id") != mission
            or entry.get("version") != index
            or entry.get("previous_hash") != previous
            or entry.get("digest") != _digest(payload)
            or entry.get("execution_authorised") is not False
        ):
            raise RuntimeError("orchestration_history_tampered_or_forked")
        previous = str(entry["digest"])
        versions.append(entry)
    return versions


def checkpoint(
    owner_id: object,
    mission: dict[str, Any],
    *,
    expected_last_hash: str = "",
    stopped: bool = False,
) -> dict[str, Any]:
    if stopped:
        raise PermissionError("STOP: orchestration checkpoint blocked")
    mission_id = str(uuid.UUID(str(mission.get("mission_id"))))
    versions = _history(owner_id, mission_id)
    previous = str(versions[-1]["digest"]) if versions else "GENESIS"
    required = previous if versions else ""
    if expected_last_hash != required:
        raise RuntimeError("stale_orchestration_version")
    version = len(versions) + 1
    safe_state = {
        "mission_id": mission_id,
        "version": version,
        "previous_hash": previous,
        "steps": mission.get("steps", ()),
        "workspace_count": int(mission.get("workspace_count") or 0),
        "checkpoint_every": 3,
        "max_steps": 21,
        "resumable": True,
        "execution_authorised": False,
        "deploy_authorised": False,
        "database_write_authorised": False,
        "publish_authorised": False,
        "distribution_authorised": False,
        "payment_authorised": False,
        "human_authority_final": True,
    }
    entry = {**safe_state, "digest": _digest(safe_state)}
    body = json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    title = f"OAP-STUDIO-ORCH:{mission_id}:v{version}"
    record_id = workspaces.add_studio_orchestration_record_atomic(
        owner_id,
        mission_id=mission_id,
        version=version,
        digest=entry["digest"],
        title=title,
        body=body,
    )
    saved = _history(owner_id, mission_id)
    latest = saved[-1]
    if latest["digest"] != entry["digest"]:
        raise RuntimeError("orchestration_checkpoint_readback_mismatch")
    return {
        "mission_id": mission_id,
        "version": version,
        "digest": entry["digest"],
        "record_id": record_id,
        "read_back_verified": True,
        "resumable": True,
        "execution_authorised": False,
    }


def resume(owner_id: object, mission_id: object) -> dict[str, Any]:
    versions = _history(owner_id, mission_id)
    if not versions:
        raise RuntimeError("orchestration_checkpoint_not_found")
    latest = versions[-1]
    return {
        **latest,
        "read_back_verified": True,
        "history_versions": len(versions),
        "execution_authorised": False,
    }



def next_handoff(owner_id: object, mission_id: object) -> dict[str, Any]:
    """Return the next eligible workspace without claiming that any step executed."""
    state = resume(owner_id, mission_id)
    steps = list(state.get("steps") or ())
    completed = {
        str(step.get("workspace"))
        for step in steps
        if str(step.get("state")) == "completed_with_proof"
    }
    for step in steps:
        workspace_id = str(step.get("workspace") or "")
        if str(step.get("state")) not in {"queued", "handoff_ready"}:
            continue
        dependencies = tuple(str(item) for item in (step.get("depends_on") or ()))
        if all(dep in completed for dep in dependencies):
            return {
                "mission_id": str(state["mission_id"]),
                "workspace": workspace_id,
                "step": int(step.get("step") or 0),
                "depends_on": dependencies,
                "preflight": studio_intelligence.workspace_preflight(workspace_id),
                "state": "handoff_ready",
                "execution_authorised": False,
                "human_authority_final": True,
            }
    return {
        "mission_id": str(state["mission_id"]),
        "workspace": None,
        "step": None,
        "state": "awaiting_proven_step_results",
        "execution_authorised": False,
        "human_authority_final": True,
    }

def status() -> dict[str, Any]:
    return {
        "component": "OAP Studio Workspace Orchestrator",
        "dependency_graph_ready": True,
        "multi_workspace_planning_ready": True,
        "owner_scoped_checkpoint_ready": True,
        "resumable_handoff_ready": True,
        "next_handoff_preflight_ready": True,
        "checkpoint_every": 3,
        "max_steps": 21,
        "execution_authorised": False,
        "consequential_execution_locked": True,
        "human_authority_final": True,
    }
