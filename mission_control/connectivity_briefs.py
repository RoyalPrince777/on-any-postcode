"""Founder-reviewed 6G/ISAC brief receipts for the SMI Organiser.

This store is an import boundary, not an external-agent execution channel. It
persists a bounded summary and primary-source links only after a Founder action.
The automation prompt, raw task output and execution authority are never stored.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import sha256
from urllib.parse import urlsplit
from uuid import UUID

from mission_control import workspaces

_LIMIT = 100
_RUN_ID = re.compile(r"^[A-Za-z0-9-]{16,80}$")
_DECISIONS = frozenset(
    {"pending_review", "adopt_for_review", "watch", "reject_insufficient_evidence"}
)


class ConnectivityBriefUnavailable(RuntimeError):
    """The brief history cannot be proven complete and untampered."""


def _owner(value: object) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("canonical_brief_owner_required") from exc


def _brief_id(value: object) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("canonical_connectivity_brief_id_required") from exc


def _digest(payload: dict[str, object]) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _valid_source_link(value: str) -> bool:
    parsed = urlsplit(value)
    return (
        value == value.strip()
        and not any(character.isspace() or ord(character) < 32 for character in value)
        and parsed.scheme == "https"
        and bool(parsed.netloc)
        and parsed.username is None
        and parsed.password is None
        and len(value) <= 500
    )


@dataclass(frozen=True)
class ConnectivityBrief:
    brief_id: str
    source_run_id: str
    title: str
    completed_at: str
    summary: str
    evidence_links: tuple[str, ...]
    evidence_score: int
    decision: str = "pending_review"
    no_material_update: bool = False
    source: str = "chatgpt_automation"

    def __post_init__(self) -> None:
        _brief_id(self.brief_id)
        if not isinstance(self.source_run_id, str) or not _RUN_ID.fullmatch(self.source_run_id):
            raise ValueError("invalid_connectivity_brief_run_id")
        if not isinstance(self.title, str) or not self.title.strip() or len(self.title) > 160:
            raise ValueError("invalid_connectivity_brief_title")
        if not isinstance(self.completed_at, str) or len(self.completed_at) > 64:
            raise ValueError("invalid_connectivity_brief_completed_at")
        try:
            completed = datetime.fromisoformat(self.completed_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("invalid_connectivity_brief_completed_at") from exc
        if completed.tzinfo is None:
            raise ValueError("connectivity_brief_timezone_required")
        if not isinstance(self.summary, str) or not self.summary.strip() or len(self.summary) > 4000:
            raise ValueError("invalid_connectivity_brief_summary")
        if not isinstance(self.evidence_links, tuple) or len(self.evidence_links) > 12:
            raise ValueError("invalid_connectivity_brief_evidence_links")
        if len(set(self.evidence_links)) != len(self.evidence_links):
            raise ValueError("duplicate_connectivity_brief_evidence_link")
        if any(not isinstance(link, str) or not _valid_source_link(link) for link in self.evidence_links):
            raise ValueError("invalid_connectivity_brief_evidence_link")
        if type(self.evidence_score) is not int or not 0 <= self.evidence_score <= 100:
            raise ValueError("invalid_connectivity_brief_evidence_score")
        if self.decision not in _DECISIONS:
            raise ValueError("invalid_connectivity_brief_decision")
        if type(self.no_material_update) is not bool:
            raise ValueError("invalid_no_material_update_state")
        if not self.evidence_links and not self.no_material_update:
            raise ValueError("connectivity_brief_evidence_required")
        if self.source != "chatgpt_automation":
            raise ValueError("unsupported_connectivity_brief_source")


def _entries(owner_id: str, brief_id: str) -> list[dict[str, object]]:
    records = workspaces.list_connectivity_brief_records(owner_id, brief_id, limit=_LIMIT)
    receipts = workspaces.list_connectivity_brief_audit_receipts(
        owner_id, brief_id, limit=_LIMIT,
    )
    if len(records) >= _LIMIT or len(receipts) >= _LIMIT:
        raise ConnectivityBriefUnavailable("connectivity_brief_history_limit_reached")
    receipt_by_version: dict[int, dict[str, object]] = {}
    for receipt in receipts:
        metadata = receipt.get("metadata")
        version = metadata.get("version") if isinstance(metadata, dict) else None
        if type(version) is not int or version in receipt_by_version:
            raise ConnectivityBriefUnavailable("connectivity_brief_receipt_invalid")
        receipt_by_version[version] = receipt
    versions: list[dict[str, object]] = []
    for record in records:
        try:
            entry = json.loads(record["body"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ConnectivityBriefUnavailable("connectivity_brief_history_unreadable") from exc
        if not isinstance(entry, dict):
            raise ConnectivityBriefUnavailable("connectivity_brief_history_invalid")
        version = entry.get("version")
        receipt = receipt_by_version.get(version) if type(version) is int else None
        metadata = receipt.get("metadata") if receipt else None
        if (
            entry.get("owner_id") != owner_id
            or entry.get("brief_id") != brief_id
            or record.get("title") != f"OAP-CONNECTIVITY-BRIEF:{brief_id}:v{version}"
            or record.get("status") != "draft"
            or not isinstance(metadata, dict)
            or receipt.get("actor_id") != owner_id
            or receipt.get("target") != f"connectivity_brief:{brief_id}"
            or metadata.get("record_id") != record.get("record_id")
            or metadata.get("digest") != entry.get("digest")
            or metadata.get("prompt_persisted") is not False
            or metadata.get("execution_authorised") is not False
            or metadata.get("founder_review_required") is not True
        ):
            raise ConnectivityBriefUnavailable("connectivity_brief_scope_or_receipt_mismatch")
        versions.append(entry)
    versions.sort(key=lambda item: item.get("version", 0))
    previous = "GENESIS"
    required_keys = {
        "owner_id", "brief_id", "version", "previous_hash", "brief",
        "prompt_persisted", "execution_authorised", "founder_review_required",
        "founder_approved", "physical_acceptance", "digest",
    }
    for index, entry in enumerate(versions, 1):
        payload = {key: value for key, value in entry.items() if key != "digest"}
        if (
            entry.get("version") != index
            or entry.get("previous_hash") != previous
            or entry.get("digest") != _digest(payload)
            or entry.get("prompt_persisted") is not False
            or entry.get("execution_authorised") is not False
            or entry.get("founder_review_required") is not True
            or entry.get("founder_approved") is not False
            or entry.get("physical_acceptance") is not False
            or set(entry) != required_keys
        ):
            raise ConnectivityBriefUnavailable("connectivity_brief_history_tampered_or_forked")
        try:
            data = dict(entry["brief"])
            data["evidence_links"] = tuple(data.get("evidence_links", ()))
            ConnectivityBrief(**data)
        except (TypeError, ValueError) as exc:
            raise ConnectivityBriefUnavailable("connectivity_brief_payload_invalid") from exc
        previous = str(entry["digest"])
    return versions


def get(owner_id: object, brief_id: object) -> dict[str, object]:
    owner = _owner(owner_id)
    brief = _brief_id(brief_id)
    versions = _entries(owner, brief)
    if not versions:
        raise ConnectivityBriefUnavailable("connectivity_brief_not_found")
    latest = versions[-1]
    return {
        "brief_id": brief,
        "version": latest["version"],
        "digest": latest["digest"],
        "brief": latest["brief"],
        "audit_readback_verified": True,
        "prompt_persisted": False,
        "execution_authorised": False,
        "founder_review_required": True,
        "founder_approved": False,
        "physical_acceptance": False,
    }


def list_all(owner_id: object, *, limit: int = 50) -> tuple[dict[str, object], ...]:
    owner = _owner(owner_id)
    brief_ids = workspaces.list_connectivity_brief_ids(owner, limit=limit)
    results = []
    for brief_id in brief_ids:
        try:
            canonical = _brief_id(brief_id)
        except ValueError as exc:
            raise ConnectivityBriefUnavailable("connectivity_brief_index_invalid") from exc
        results.append(get(owner, canonical))
    return tuple(results)


def upsert(
    owner_id: object,
    brief: ConnectivityBrief,
    *,
    expected_last_hash: str = "",
    stopped: bool = False,
) -> dict[str, object]:
    if type(stopped) is not bool or stopped:
        raise PermissionError("STOP: connectivity brief import blocked")
    if not isinstance(brief, ConnectivityBrief):
        raise TypeError("typed_connectivity_brief_required")
    owner = _owner(owner_id)
    brief_id = _brief_id(brief.brief_id)
    versions = _entries(owner, brief_id)
    previous = str(versions[-1]["digest"]) if versions else "GENESIS"
    required_hash = previous if versions else ""
    if expected_last_hash != required_hash:
        raise ConnectivityBriefUnavailable("stale_connectivity_brief_version")
    brief_data = asdict(brief)
    brief_data["evidence_links"] = list(brief.evidence_links)
    if versions and versions[-1].get("brief") == brief_data:
        return {**get(owner, brief_id), "changed": False}
    version = len(versions) + 1
    payload: dict[str, object] = {
        "owner_id": owner,
        "brief_id": brief_id,
        "version": version,
        "previous_hash": previous,
        "brief": brief_data,
        "prompt_persisted": False,
        "execution_authorised": False,
        "founder_review_required": True,
        "founder_approved": False,
        "physical_acceptance": False,
    }
    entry = {**payload, "digest": _digest(payload)}
    body = json.dumps(entry, sort_keys=True, separators=(",", ":"), allow_nan=False)
    workspaces.add_connectivity_brief_record_atomic(
        owner,
        brief_id=brief_id,
        version=version,
        digest=str(entry["digest"]),
        title=f"OAP-CONNECTIVITY-BRIEF:{brief_id}:v{version}",
        body=body,
    )
    saved = get(owner, brief_id)
    if saved["digest"] != entry["digest"] or saved["version"] != version:
        raise ConnectivityBriefUnavailable("connectivity_brief_write_readback_mismatch")
    return {**saved, "changed": True}
