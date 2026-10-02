"""OAP-wide evidence fabric for whole-company truth and resilience.

This is the whole-organism 700-check view:
14 OAP domains x 10 intelligence lenses x 5 universal proof classes = 700 cells.

It does not replace deeper subsystem registries such as Company Intelligence.
It gives SMI and Human Authority one fail-closed cross-OAP control plane.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Any

OAP_DOMAINS: tuple[str, ...] = (
    "infrastructure",
    "trust_identity",
    "world_spot",
    "link_up",
    "music",
    "commerce_market",
    "sika",
    "post_core",
    "movement",
    "media_studio",
    "youth",
    "nature",
    "arena",
    "intelligence_governance",
)

INTELLIGENCE_LENSES: tuple[str, ...] = (
    "truth",
    "evidence",
    "risk",
    "dependency",
    "architecture",
    "security",
    "privacy",
    "compliance",
    "commercial_value",
    "recovery",
)

PROOF_CLASSES: tuple[str, ...] = (
    "source_and_version",
    "functional_runtime",
    "permission_and_authority",
    "integration_and_dependency",
    "recovery_and_readback",
)

CELL_STATES = ("PASS", "FAIL", "CONFLICTING", "UNKNOWN", "N/A")
_RESOLVED = {"PASS", "N/A"}


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


def catalogue() -> tuple[dict[str, str], ...]:
    return tuple(
        {
            "check_id": f"OAP-{index:03d}",
            "domain": domain,
            "lens": lens,
            "proof_class": proof_class,
        }
        for index, (domain, lens, proof_class) in enumerate(
            (
                (domain, lens, proof_class)
                for domain in OAP_DOMAINS
                for lens in INTELLIGENCE_LENSES
                for proof_class in PROOF_CLASSES
            ),
            start=1,
        )
    )


def _normalize_receipt(
    receipt: Mapping[str, object],
    known_ids: set[str],
) -> dict[str, Any] | None:
    check_id = str(receipt.get("check_id") or "").strip().upper()
    state = str(receipt.get("state") or "").strip().upper()
    evidence_reference = str(receipt.get("evidence_reference") or "").strip()[:500]
    source_system = str(receipt.get("source_system") or "").strip()[:120]
    failure_reason = str(receipt.get("failure_reason") or "").strip()[:500]
    recovery_requirement = str(
        receipt.get("recovery_requirement") or ""
    ).strip()[:500]
    observed_at = _timestamp(receipt.get("observed_at"))

    if (
        check_id not in known_ids
        or state not in CELL_STATES
        or not evidence_reference
        or not source_system
        or observed_at is None
    ):
        return None

    return {
        "check_id": check_id,
        "state": state,
        "evidence_reference": evidence_reference,
        "source_system": source_system,
        "failure_reason": failure_reason,
        "recovery_requirement": recovery_requirement,
        "observed_at": observed_at.isoformat(),
    }


def snapshot(
    receipts: Iterable[Mapping[str, object]] = (),
    *,
    founder_final_recorded: bool = False,
) -> dict[str, Any]:
    cells = catalogue()
    definitions = {cell["check_id"]: cell for cell in cells}
    latest: dict[str, dict[str, Any]] = {}
    invalid = 0

    for raw in receipts:
        item = _normalize_receipt(raw, set(definitions))
        if item is None:
            invalid += 1
            continue
        current = latest.get(item["check_id"])
        if current is None or item["observed_at"] > current["observed_at"]:
            latest[item["check_id"]] = item

    projected: list[dict[str, Any]] = []
    for check_id, definition in definitions.items():
        receipt = latest.get(check_id)
        projected.append(
            {
                **definition,
                "state": receipt["state"] if receipt else "UNKNOWN",
                "evidence_reference": receipt["evidence_reference"] if receipt else "",
                "source_system": receipt["source_system"] if receipt else "",
                "observed_at": receipt["observed_at"] if receipt else None,
                "failure_reason": receipt["failure_reason"] if receipt else "",
                "recovery_requirement": (
                    receipt["recovery_requirement"] if receipt else ""
                ),
            }
        )

    counts = {
        state: sum(cell["state"] == state for cell in projected)
        for state in CELL_STATES
    }
    domain_status: dict[str, dict[str, Any]] = {}
    for domain in OAP_DOMAINS:
        domain_cells = [cell for cell in projected if cell["domain"] == domain]
        domain_counts = {
            state: sum(cell["state"] == state for cell in domain_cells)
            for state in CELL_STATES
        }
        resolved = domain_counts["PASS"] + domain_counts["N/A"]
        domain_status[domain] = {
            "total": len(domain_cells),
            "counts": domain_counts,
            "resolved": resolved,
            "green": (
                resolved == len(domain_cells)
                and domain_counts["FAIL"] == 0
                and domain_counts["CONFLICTING"] == 0
                and domain_counts["UNKNOWN"] == 0
            ),
        }

    resolved = counts["PASS"] + counts["N/A"]
    green_gate = (
        resolved == len(projected)
        and counts["FAIL"] == 0
        and counts["CONFLICTING"] == 0
        and counts["UNKNOWN"] == 0
    )
    return {
        "registry": "OAP Whole-Company Evidence Fabric",
        "domain_count": len(OAP_DOMAINS),
        "lens_count": len(INTELLIGENCE_LENSES),
        "proof_class_count": len(PROOF_CLASSES),
        "protocol_check_count": len(projected),
        "cells": tuple(projected),
        "counts": counts,
        "domain_status": domain_status,
        "valid_receipt_count": len(latest),
        "invalid_receipt_count": invalid,
        "proven_count": counts["PASS"],
        "resolved_count": resolved,
        "proven_percentage": round((counts["PASS"] / len(projected)) * 100, 1),
        "resolved_percentage": round((resolved / len(projected)) * 100, 1),
        "green_gate_passed": green_gate,
        "founder_final_recorded": bool(founder_final_recorded),
        "full_green": green_gate and bool(founder_final_recorded),
        "missing_defaults_to_unknown": True,
        "subsystem_registries_remain_authoritative": True,
        "evidence_presence_grants_execution": False,
        "human_authority_final": True,
    }


def status() -> dict[str, Any]:
    empty = snapshot()
    return {
        "name": empty["registry"],
        "domain_count": empty["domain_count"],
        "protocol_check_count": empty["protocol_check_count"],
        "domains": OAP_DOMAINS,
        "lenses": INTELLIGENCE_LENSES,
        "proof_classes": PROOF_CLASSES,
        "cell_states": CELL_STATES,
        "stable_ids": True,
        "missing_defaults_to_unknown": True,
        "subsystem_registries_remain_authoritative": True,
        "founder_final_required": True,
        "full_green": False,
    }
