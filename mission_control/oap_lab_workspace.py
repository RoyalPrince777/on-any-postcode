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
    prefix = f"{_PREFIX}{notebook_id}:"
    records = workspaces.list_records_with_title_prefix(
        owner_id, _WORKSPACE, title_prefix=prefix, limit=_LIMIT,
    )
    receipts = workspaces.list_lab_audit_receipts(
        owner_id, notebook_id, limit=_LIMIT,
    )
    if len(records) >= _LIMIT or len(receipts) >= _LIMIT:
        raise NotebookHistoryUnavailable("workspace_history_limit_reached")
    receipt_by_version: dict[int, dict[str, object]] = {}
    for receipt in receipts:
        metadata = receipt.get("metadata")
        if not isinstance(metadata, dict) or type(metadata.get("version")) is not int:
            raise NotebookHistoryUnavailable("notebook_audit_receipt_invalid")
        version = metadata["version"]
        if version in receipt_by_version:
            raise NotebookHistoryUnavailable("notebook_audit_receipt_duplicate")
        receipt_by_version[version] = receipt
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
        # A matching body alone is insufficient: the first-party record title
        # must identify exactly the same version, and no authority can be
        # restored through extra or silently altered notebook fields.
        if record.get("status") != "draft":
            raise NotebookHistoryUnavailable("notebook_workspace_status_invalid")
        receipt = receipt_by_version.get(entry.get("version"))
        if receipt is None:
            raise NotebookHistoryUnavailable("notebook_audit_receipt_missing")
        metadata = receipt["metadata"]
        if (
            receipt.get("actor_id") != owner_id
            or receipt.get("target") != f"oap_lab_notebook:{notebook_id}"
            or metadata.get("workspace_id") != "governance"
            or metadata.get("notebook_id") != notebook_id
            or metadata.get("record_id") != record.get("record_id")
            or metadata.get("digest") != entry.get("digest")
            or metadata.get("record_status") != "draft"
            or metadata.get("publication_authorised") is not False
            or metadata.get("execution_authorised") is not False
        ):
            raise NotebookHistoryUnavailable("notebook_audit_receipt_mismatch")
        if record["title"] != f"{prefix}v{entry.get('version')}":
            raise NotebookHistoryUnavailable("notebook_version_title_mismatch")
        if (
            entry.get("state") != "research_draft"
            or any(entry.get(key) is not False for key in (
                "publication_authorised", "execution_authorised",
                "scientific_truth_established",
            ))
            or set(entry) != {
                "owner_id", "notebook_id", "version", "previous_hash",
                "notebook", "state", "publication_authorised",
                "execution_authorised", "scientific_truth_established",
                "digest",
            }
            or not isinstance(entry.get("notebook"), dict)
            or set(entry["notebook"]) != {
                "mission", "domain", "question", "hypothesis",
                "falsification",
            }
        ):
            raise NotebookHistoryUnavailable("notebook_review_scope_invalid")
        versions.append(entry)
    if any(type(item.get("version")) is not int for item in versions):
        raise NotebookHistoryUnavailable("notebook_history_version_invalid")
    versions.sort(key=lambda item: item["version"])
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
    try:
        Notebook(identifier=notebook, **{
            key: data[key] for key in (
                "mission", "domain", "question", "hypothesis",
                "falsification",
            )
        })
    except (TypeError, ValueError) as exc:
        raise NotebookHistoryUnavailable("notebook_history_invalid") from exc
    return {
        "notebook_id": notebook, "version": latest["version"],
        "digest": latest["digest"], "notebook": data,
        "workspace_record_persisted": True,
        "atomic_audit_write_contract": True,
        "audit_readback_verified": True,
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
    workspaces.add_lab_record_atomic(
        owner,
        title=f"{_PREFIX}{notebook_id}:v{version}",
        body=body,
        notebook_id=notebook_id,
        version=version,
        digest=entry["digest"],
    )
    saved = reopen(owner, notebook_id)
    if saved["digest"] != entry["digest"] or saved["version"] != version:
        raise NotebookHistoryUnavailable("notebook_write_readback_mismatch")
    return saved
