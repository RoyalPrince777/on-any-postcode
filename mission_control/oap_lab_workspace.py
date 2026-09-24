"""OAP LAB notebook versions in the existing owner-scoped My World governance store.

This adapter does not create tables, independently retained anchors, or
immutable database guarantees. It fails closed if the bounded workspace
listing cannot establish a complete, untampered, linear notebook history.
"""
from __future__ import annotations

import json
from hashlib import sha256
from uuid import UUID

from mission_control import workspaces
from mission_control.oap_lab_research import Notebook

_PREFIX = "OAP-LAB:"
_WORKSPACE = "governance"
_LIMIT = 100


class NotebookHistoryUnavailable(RuntimeError):
    """Existing store cannot prove a complete owner-scoped notebook view."""


def _uuid(value: object) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("canonical_notebook_or_owner_id_required") from exc


def _hash(payload: dict[str, object]) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _entries(owner_id: str, notebook_id: str) -> list[dict[str, object]]:
    records = workspaces.list_records(owner_id, _WORKSPACE, limit=_LIMIT)
    if len(records) >= _LIMIT:
        raise NotebookHistoryUnavailable("workspace_history_limit_reached")
    prefix = f"{_PREFIX}{notebook_id}:"
    versions = []
    for record in records:
        if not record["title"].startswith(prefix):
            continue
        try:
            entry = json.loads(record["body"])
        except (TypeError, ValueError) as exc:
            raise NotebookHistoryUnavailable("notebook_history_unreadable") from exc
        if not isinstance(entry, dict) or entry.get("owner_id") != owner_id or (
            entry.get("notebook_id") != notebook_id
        ):
            raise NotebookHistoryUnavailable("notebook_history_scope_mismatch")
        versions.append(entry)
    versions.sort(key=lambda item: item.get("version", -1))
    previous = "GENESIS"
    for index, entry in enumerate(versions, 1):
        digest = entry.get("digest")
        payload = {k: v for k, v in entry.items() if k != "digest"}
        if (entry.get("version") != index or entry.get("previous_hash") != previous
                or digest != _hash(payload) or not isinstance(entry.get("notebook"), dict)):
            raise NotebookHistoryUnavailable("notebook_history_tampered_or_forked")
        previous = digest
    return versions


def reopen(owner_id: object, notebook_id: object) -> dict[str, object]:
    owner, notebook = _uuid(owner_id), _uuid(notebook_id)
    versions = _entries(owner, notebook)
    if not versions:
        raise NotebookHistoryUnavailable("notebook_not_found")
    latest = versions[-1]
    data = latest["notebook"]
    if any(not isinstance(data.get(key), str) for key in (
        "mission", "domain", "question", "hypothesis", "falsification",
    )):
        raise NotebookHistoryUnavailable("notebook_history_invalid")
    # Validate against the original LAB research contract, never elevate state.
    Notebook(identifier=notebook, **{
        key: data[key] for key in (
            "mission", "domain", "question", "hypothesis", "falsification",
        )
    })
    return {
        "notebook_id": notebook, "version": latest["version"],
        "digest": latest["digest"], "notebook": data,
        "workspace_record_persisted": True,
        "immutable_history_verified": False,
        "independent_recovery_verified": False,
        "release_ready": False,
    }


def save(
    owner_id: object, notebook: Notebook, *, expected_last_hash: str = "",
    stopped: bool = False,
) -> dict[str, object]:
    if type(stopped) is not bool or stopped:
        raise PermissionError("STOP: notebook save blocked")
    if not isinstance(notebook, Notebook):
        raise TypeError("typed_lab_notebook_required")
    owner, notebook_id = _uuid(owner_id), _uuid(notebook.identifier)
    versions = _entries(owner, notebook_id)
    previous = versions[-1]["digest"] if versions else "GENESIS"
    if expected_last_hash != (previous if versions else ""):
        raise NotebookHistoryUnavailable("stale_notebook_version")
    version = len(versions) + 1
    if version >= _LIMIT:
        raise NotebookHistoryUnavailable("notebook_version_limit_reached")
    payload = {
        "owner_id": owner, "notebook_id": notebook_id,
        "version": version, "previous_hash": previous,
        "notebook": {
            "mission": notebook.mission, "domain": notebook.domain,
            "question": notebook.question, "hypothesis": notebook.hypothesis,
            "falsification": notebook.falsification,
        },
        "state": "research_draft", "publication_authorised": False,
        "execution_authorised": False, "scientific_truth_established": False,
    }
    entry = {**payload, "digest": _hash(payload)}
    body = json.dumps(entry, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if len(body) > 5000:
        raise ValueError("notebook_exceeds_workspace_limit")
    workspaces.add_record(
        owner, _WORKSPACE, title=f"{_PREFIX}{notebook_id}:v{version}",
        body=body, status="draft",
    )
    saved = reopen(owner, notebook_id)
    if saved["digest"] != entry["digest"] or saved["version"] != version:
        raise NotebookHistoryUnavailable("notebook_write_readback_mismatch")
    return saved
