"""Owner-scoped mirror of external schedules in the SMI Organiser.

The mirror is deliberately metadata-minimal: it stores the external schedule
identifier, title and timing contract, but never stores the automation prompt
or task output.  Each change is append-only and must have a matching audit
receipt before it can be returned to a caller.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from hashlib import sha256
from uuid import UUID

from mission_control import workspaces

_PREFIX = "OAP-ORGANISER-SCHEDULE:"
_LIMIT = 100
_ID = re.compile(r"^[A-Za-z0-9-]{16,80}$")
_TIMEZONE = re.compile(r"^[A-Za-z_]+(?:/[A-Za-z0-9_+.-]+)+$")
_TIMING_MODES = frozenset({"exact_schedule", "flexible_schedule", "condition_watch"})


class ScheduleMirrorUnavailable(RuntimeError):
    """The Organiser cannot prove a complete, untampered schedule history."""


def _owner(value: object) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("canonical_schedule_owner_required") from exc


def _digest(payload: dict[str, object]) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


@dataclass(frozen=True)
class OrganiserSchedule:
    external_id: str
    title: str
    schedule: str
    timing_mode: str
    timezone: str = "Europe/London"
    enabled: bool = True
    source: str = "chatgpt_automation"

    def __post_init__(self) -> None:
        if not isinstance(self.external_id, str) or not _ID.fullmatch(self.external_id):
            raise ValueError("invalid_external_schedule_id")
        if not isinstance(self.title, str) or not self.title.strip() or len(self.title) > 120:
            raise ValueError("invalid_schedule_title")
        if self.source != "chatgpt_automation":
            raise ValueError("unsupported_schedule_source")
        if self.timing_mode not in _TIMING_MODES:
            raise ValueError("invalid_schedule_timing_mode")
        if type(self.enabled) is not bool:
            raise ValueError("invalid_schedule_enabled_state")
        if (
            not isinstance(self.timezone, str)
            or len(self.timezone) > 64
            or not _TIMEZONE.fullmatch(self.timezone)
        ):
            raise ValueError("invalid_schedule_timezone")
        if (
            not isinstance(self.schedule, str)
            or len(self.schedule) > 1200
            or not self.schedule.startswith("BEGIN:VEVENT\n")
            or not self.schedule.endswith("\nEND:VEVENT")
            or "\x00" in self.schedule
        ):
            raise ValueError("invalid_ical_schedule")


def _entries(owner_id: str, external_id: str) -> list[dict[str, object]]:
    prefix = f"{_PREFIX}{external_id}:"
    records = workspaces.list_organiser_schedule_records(
        owner_id, external_id, limit=_LIMIT,
    )
    receipts = workspaces.list_organiser_schedule_audit_receipts(
        owner_id, external_id, limit=_LIMIT,
    )
    if len(records) >= _LIMIT or len(receipts) >= _LIMIT:
        raise ScheduleMirrorUnavailable("schedule_history_limit_reached")
    receipt_by_version: dict[int, dict[str, object]] = {}
    for receipt in receipts:
        metadata = receipt.get("metadata")
        version = metadata.get("version") if isinstance(metadata, dict) else None
        if type(version) is not int or version in receipt_by_version:
            raise ScheduleMirrorUnavailable("schedule_audit_receipt_invalid")
        receipt_by_version[version] = receipt
    versions: list[dict[str, object]] = []
    for record in records:
        try:
            entry = json.loads(record["body"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ScheduleMirrorUnavailable("schedule_history_unreadable") from exc
        if not isinstance(entry, dict):
            raise ScheduleMirrorUnavailable("schedule_history_invalid")
        version = entry.get("version")
        receipt = receipt_by_version.get(version) if type(version) is int else None
        metadata = receipt.get("metadata") if receipt else None
        if (
            entry.get("owner_id") != owner_id
            or entry.get("external_id") != external_id
            or record.get("title") != f"{prefix}v{version}"
            or record.get("status") != "draft"
            or not isinstance(metadata, dict)
            or receipt.get("actor_id") != owner_id
            or receipt.get("target") != f"smi_organiser_schedule:{external_id}"
            or metadata.get("record_id") != record.get("record_id")
            or metadata.get("digest") != entry.get("digest")
            or metadata.get("prompt_persisted") is not False
            or metadata.get("execution_authorised") is not False
        ):
            raise ScheduleMirrorUnavailable("schedule_scope_or_receipt_mismatch")
        versions.append(entry)
    versions.sort(key=lambda item: item.get("version", 0))
    previous = "GENESIS"
    for index, entry in enumerate(versions, 1):
        payload = {key: value for key, value in entry.items() if key != "digest"}
        if (
            entry.get("version") != index
            or entry.get("previous_hash") != previous
            or entry.get("digest") != _digest(payload)
            or entry.get("prompt_persisted") is not False
            or entry.get("execution_authorised") is not False
            or set(entry) != {
                "owner_id", "external_id", "version", "previous_hash", "schedule",
                "prompt_persisted", "execution_authorised", "digest",
            }
        ):
            raise ScheduleMirrorUnavailable("schedule_history_tampered_or_forked")
        try:
            OrganiserSchedule(**entry["schedule"])
        except (TypeError, ValueError) as exc:
            raise ScheduleMirrorUnavailable("schedule_payload_invalid") from exc
        previous = str(entry["digest"])
    return versions


def get(owner_id: object, external_id: object) -> dict[str, object]:
    owner = _owner(owner_id)
    schedule_id = str(external_id or "")
    if not _ID.fullmatch(schedule_id):
        raise ValueError("invalid_external_schedule_id")
    versions = _entries(owner, schedule_id)
    if not versions:
        raise ScheduleMirrorUnavailable("schedule_not_found")
    latest = versions[-1]
    return {
        "external_id": schedule_id,
        "version": latest["version"],
        "digest": latest["digest"],
        "schedule": latest["schedule"],
        "audit_readback_verified": True,
        "prompt_persisted": False,
        "execution_authorised": False,
    }


def upsert(
    owner_id: object,
    schedule: OrganiserSchedule,
    *,
    expected_last_hash: str = "",
    stopped: bool = False,
) -> dict[str, object]:
    if type(stopped) is not bool or stopped:
        raise PermissionError("STOP: schedule mirror blocked")
    if not isinstance(schedule, OrganiserSchedule):
        raise TypeError("typed_organiser_schedule_required")
    owner = _owner(owner_id)
    versions = _entries(owner, schedule.external_id)
    previous = str(versions[-1]["digest"]) if versions else "GENESIS"
    required_hash = previous if versions else ""
    if expected_last_hash != required_hash:
        raise ScheduleMirrorUnavailable("stale_schedule_version")
    schedule_data = asdict(schedule)
    if versions and versions[-1].get("schedule") == schedule_data:
        return {**get(owner, schedule.external_id), "changed": False}
    version = len(versions) + 1
    payload: dict[str, object] = {
        "owner_id": owner,
        "external_id": schedule.external_id,
        "version": version,
        "previous_hash": previous,
        "schedule": schedule_data,
        "prompt_persisted": False,
        "execution_authorised": False,
    }
    entry = {**payload, "digest": _digest(payload)}
    body = json.dumps(entry, sort_keys=True, separators=(",", ":"), allow_nan=False)
    workspaces.add_organiser_schedule_record_atomic(
        owner,
        external_id=schedule.external_id,
        version=version,
        digest=str(entry["digest"]),
        title=f"{_PREFIX}{schedule.external_id}:v{version}",
        body=body,
    )
    saved = get(owner, schedule.external_id)
    if saved["digest"] != entry["digest"] or saved["version"] != version:
        raise ScheduleMirrorUnavailable("schedule_write_readback_mismatch")
    return {**saved, "changed": True}
