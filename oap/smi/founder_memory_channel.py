"""Audited repository-backed Founder memory channel for SMI.

This is the concrete transport available to the current ChatGPT/GitHub workflow:
Founder-approved packets are committed to the repository, validated by the same
memory-sync contract, certified by CI, and loaded by SMI after deployment.

It is intentionally not described as a direct ChatGPT HTTP connection. Raw chat is
never scraped or auto-ingested, and no packet becomes canonical automatically.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from oap.contracts import MemoryItem, OutputState

from .memory_sync import MemorySyncPacket, validate_packet

CHANNEL_REVISION = "2026-09-04-v2"
_INBOX_PATH = Path(__file__).with_name("founder_memory_inbox.json")


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in value.casefold().replace("/", " ").replace("-", " ").split()
        if len(token) > 2
    }


def _load_records() -> tuple[dict[str, Any], ...]:
    try:
        payload = json.loads(_INBOX_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()
    if not isinstance(payload, list):
        return ()
    return tuple(item for item in payload if isinstance(item, dict))


def _validate_record(record: dict[str, Any]) -> dict[str, Any]:
    packet = MemorySyncPacket(
        source_kind=str(record.get("source_kind") or ""),
        memory_class=str(record.get("memory_class") or ""),
        summary=str(record.get("summary") or ""),
        source_reference=str(record.get("source_reference") or ""),
        founder_approved=record.get("founder_approved") is True,
        supersedes=tuple(str(item) for item in record.get("supersedes") or ()),
        tags=tuple(str(item) for item in record.get("tags") or ()),
    )
    result = validate_packet(packet)
    result["created_at"] = str(record.get("created_at") or "")
    return result


def synced_memory_items(
    task_type: str | None = None,
    *,
    query: str = "",
    limit: int = 3,
) -> tuple[MemoryItem, ...]:
    """Return approved, validated Founder-channel memory as non-canonical context."""

    safe_limit = min(max(int(limit), 1), 6)
    query_tokens = _tokens(query)
    candidates: list[tuple[int, int, dict[str, Any]]] = []
    for index, record in enumerate(_load_records()):
        validated = _validate_record(record)
        if not validated.get("accepted_as_candidate"):
            continue
        searchable = " ".join(
            (
                str(validated.get("summary") or ""),
                " ".join(validated.get("tags") or ()),
                str(validated.get("memory_class") or ""),
                str(task_type or ""),
            )
        )
        score = len(query_tokens & _tokens(searchable)) if query_tokens else 0
        # Latest Founder-approved packet wins on relevance ties.
        candidates.append((score, index, validated))
    candidates.sort(reverse=True)
    selected = [item[2] for item in candidates[:safe_limit]]
    memories: list[MemoryItem] = []
    for item in selected:
        created_at = _parse_created_at(str(item.get("created_at") or ""))
        memory_class = str(item.get("memory_class") or "SYNC")
        memories.append(
            MemoryItem(
                memory_id=f"founder-sync:{str(item.get('digest') or '')[:16]}",
                task_type=f"FOUNDER_SYNC_{memory_class}",
                summary=(
                    "FOUNDER-APPROVED SYNC CONTEXT — "
                    + str(item.get("summary") or "")
                    + " Canonical promotion remains separate and audited."
                ),
                output_state=OutputState.SYSTEM_LOG_ONLY.value,
                created_at=created_at,
            )
        )
    return tuple(memories)


def _parse_created_at(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return datetime(2026, 9, 4, tzinfo=timezone.utc)


def status() -> dict[str, object]:
    records = _load_records()
    validated = tuple(_validate_record(item) for item in records)
    accepted = sum(bool(item.get("accepted_as_candidate")) for item in validated)
    rejected = len(validated) - accepted
    return {
        "component": "SMI Founder Memory Channel",
        "ready": bool(records) and rejected == 0,
        "revision": CHANNEL_REVISION,
        "transport": "github_audited_repository_channel",
        "github_audited_transport_connected": True,
        "direct_chatgpt_http_connected": False,
        "always_on_raw_chat_sync": False,
        "packet_count": len(records),
        "accepted_packet_count": accepted,
        "rejected_packet_count": rejected,
        "latest_relevant_founder_packet_wins_ties": True,
        "automatic_canonical_promotion": False,
        "founder_approval_required": True,
        "ci_and_deploy_required": True,
        "human_authority_final": True,
    }
