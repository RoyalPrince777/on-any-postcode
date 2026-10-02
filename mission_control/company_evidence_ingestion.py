"""Fail-closed evidence ingestion for OAP Company Intelligence.

This module normalizes externally obtained company/commercial evidence into a
single read-only review snapshot. It does not fetch third-party systems by itself,
does not verify law/rights by assertion, and never turns evidence presence into
execution authority.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Any

DOMAINS = (
    "company_registry",
    "artist_rights",
    "music_catalogue",
    "clothing_supplier",
    "print_on_demand_supplier",
    "pricing_margin",
    "market_commerce",
)

ACCEPTED_STATES = {"PROVEN", "CONFLICTING", "STALE", "UNAVAILABLE", "UNKNOWN"}
MAX_REF = 500
MAX_NOTE = 500


def _clean(value: object, limit: int) -> str:
    return " ".join(str(value or "").split())[:limit]


def _timestamp(value: object) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def normalize_evidence(item: Mapping[str, object]) -> dict[str, Any]:
    domain = _clean(item.get("domain"), 80)
    state = _clean(item.get("state"), 40).upper()
    source = _clean(item.get("source_reference"), MAX_REF)
    authority = _clean(item.get("authority_reference"), MAX_REF)
    note = _clean(item.get("note"), MAX_NOTE)
    observed_at = _timestamp(item.get("observed_at"))

    valid = bool(
        domain in DOMAINS
        and state in ACCEPTED_STATES
        and source
        and observed_at is not None
    )
    return {
        "domain": domain,
        "state": state if state in ACCEPTED_STATES else "UNKNOWN",
        "source_reference": source,
        "authority_reference": authority,
        "note": note,
        "observed_at": observed_at.isoformat() if observed_at else None,
        "valid": valid,
    }


def ingest_snapshot(items: Iterable[Mapping[str, object]]) -> dict[str, Any]:
    normalized = tuple(normalize_evidence(item) for item in items)
    valid = tuple(item for item in normalized if item["valid"])
    latest: dict[str, dict[str, Any]] = {}

    for item in valid:
        domain = str(item["domain"])
        current = latest.get(domain)
        if current is None or str(item["observed_at"]) > str(current["observed_at"]):
            latest[domain] = item

    states = {
        domain: latest.get(
            domain,
            {
                "domain": domain,
                "state": "UNKNOWN",
                "source_reference": "",
                "authority_reference": "",
                "note": "",
                "observed_at": None,
                "valid": False,
            },
        )
        for domain in DOMAINS
    }

    proven = tuple(
        domain for domain, item in states.items() if item["state"] == "PROVEN"
    )
    unresolved = tuple(
        domain for domain, item in states.items() if item["state"] != "PROVEN"
    )

    commercial_ready = all(
        states[domain]["state"] == "PROVEN"
        for domain in (
            "pricing_margin",
            "market_commerce",
        )
    )
    music_ready = all(
        states[domain]["state"] == "PROVEN"
        for domain in (
            "artist_rights",
            "music_catalogue",
        )
    )
    pod_ready = all(
        states[domain]["state"] == "PROVEN"
        for domain in (
            "clothing_supplier",
            "print_on_demand_supplier",
            "pricing_margin",
        )
    )

    return {
        "domain_count": len(DOMAINS),
        "valid_evidence_count": len(valid),
        "invalid_evidence_count": len(normalized) - len(valid),
        "states": states,
        "proven_domains": proven,
        "unresolved_domains": unresolved,
        "company_registry_proven": states["company_registry"]["state"] == "PROVEN",
        "music_evidence_ready": music_ready,
        "pod_evidence_ready": pod_ready,
        "commercial_evidence_ready": commercial_ready,
        "all_domains_proven": len(proven) == len(DOMAINS),
        "evidence_presence_is_not_legal_authority": True,
        "evidence_presence_is_not_rights_adjudication": True,
        "evidence_presence_is_not_regulatory_permission": True,
        "external_action_taken": False,
        "founder_final_required": True,
        "full_green": False,
    }


def status() -> dict[str, Any]:
    empty = ingest_snapshot(())
    return {
        "name": "OAP Company Intelligence Evidence Ingestion",
        "domains": DOMAINS,
        "accepted_states": tuple(sorted(ACCEPTED_STATES)),
        "fail_closed": True,
        "missing_evidence_defaults_to_unknown": True,
        "source_reference_required": True,
        "timestamp_required": True,
        "founder_final_required": True,
        "full_green": False,
        "empty_snapshot": empty,
    }
