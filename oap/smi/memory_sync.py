"""Governed intake contract for future external OAP memory synchronisation.

This module does not create a public ingestion endpoint and does not scrape raw
chat. It validates explicit Founder-approved decision packets and produces a
bounded candidate that can enter the normal Human Authority/audit path.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

ALLOWED_SOURCE_KINDS = frozenset(
    {
        "founder_decision",
        "approved_historical_backfill",
        "approved_chat_export",
        "approved_document_import",
    }
)
ALLOWED_MEMORY_CLASSES = frozenset(
    {
        "CANONICAL_CANDIDATE",
        "HISTORICAL",
        "ARCHITECTURE",
        "PRODUCT",
        "AGENT",
        "INFRASTRUCTURE",
        "RESEARCH",
        "EVIDENCE",
    }
)
MAX_SUMMARY_CHARS = 2000


@dataclass(frozen=True)
class MemorySyncPacket:
    source_kind: str
    memory_class: str
    summary: str
    source_reference: str
    founder_approved: bool
    supersedes: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()


def validate_packet(packet: MemorySyncPacket) -> dict[str, Any]:
    """Validate one explicit sync packet without persisting or promoting it."""

    source_kind = packet.source_kind.strip().casefold()
    memory_class = packet.memory_class.strip().upper()
    summary = " ".join(packet.summary.split())
    source_reference = packet.source_reference.strip()
    errors: list[str] = []
    if source_kind not in ALLOWED_SOURCE_KINDS:
        errors.append("source_kind_not_allowed")
    if memory_class not in ALLOWED_MEMORY_CLASSES:
        errors.append("memory_class_not_allowed")
    if not packet.founder_approved:
        errors.append("founder_approval_required")
    if not summary or len(summary) > MAX_SUMMARY_CHARS:
        errors.append("summary_invalid")
    if not source_reference or len(source_reference) > 500:
        errors.append("source_reference_invalid")

    digest_payload = {
        "source_kind": source_kind,
        "memory_class": memory_class,
        "summary": summary,
        "source_reference": source_reference,
        "supersedes": list(packet.supersedes),
        "tags": list(packet.tags),
    }
    digest = hashlib.sha256(
        json.dumps(
            digest_payload,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return {
        "accepted_as_candidate": not errors,
        "errors": tuple(errors),
        "digest": digest,
        "source_kind": source_kind,
        "memory_class": memory_class,
        "summary": summary[:MAX_SUMMARY_CHARS],
        "source_reference": source_reference,
        "supersedes": tuple(packet.supersedes),
        "tags": tuple(packet.tags),
        "automatic_canonical_promotion": False,
        "requires_audit": True,
        "requires_human_authority": True,
        "raw_chat_auto_ingestion": False,
    }


def status() -> dict[str, object]:
    return {
        "component": "SMI Governed Memory Sync",
        "ready": True,
        "packet_contract_ready": True,
        "founder_approval_required": True,
        "audit_required": True,
        "automatic_canonical_promotion": False,
        "raw_chat_auto_ingestion": False,
        "public_ingestion_endpoint": False,
        "direct_chatgpt_transport_connected": False,
        "transport_state": "explicit_audited_import_required",
        "human_authority_final": True,
    }
