"""First-party SIKA Human Rights decision gate.

This module turns the SIKA human-rights architecture into a bounded software
control. It does not determine legal compliance, regulatory status, guilt,
ownership transfer, confiscation authority, or entitlement. It validates that
consequential SIKA actions carry the minimum rights-control evidence needed
before execution and fails closed to REVIEW when that evidence is incomplete.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import datetime
from typing import Any

RIGHTS_DIMENSIONS = (
    "dignity",
    "equality",
    "privacy",
    "property",
    "accessibility",
    "due_process",
    "remedy",
    "necessity",
    "proportionality",
    "legal_authority",
)

CONSEQUENTIAL_ACTIONS = frozenset({
    "payment_decline",
    "payment_hold",
    "account_restriction",
    "account_freeze",
    "account_closure",
    "fraud_escalation",
    "identity_restriction",
    "humanitarian_payment_block",
})

DECISIONS = ("ALLOW", "REVIEW", "BLOCK")
MAX_TEXT = 280


def _clean_text(value: object, field: str, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str):
        raise TypeError(f"invalid_{field}")
    cleaned = " ".join(value.split())
    if not cleaned or len(cleaned) > MAX_TEXT:
        raise ValueError(f"invalid_{field}")
    return cleaned


def _instant(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"invalid_{field}")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError(f"invalid_{field}")
    return parsed.isoformat()


def _canonical_json(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _decision_hash(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


def canonical_rights_record(record: object) -> dict[str, Any]:
    if not isinstance(record, Mapping):
        raise TypeError("invalid_rights_record")

    action = _clean_text(record.get("action"), "action")
    if action not in CONSEQUENTIAL_ACTIONS:
        raise ValueError("unsupported_consequential_action")

    rights = record.get("rights")
    if not isinstance(rights, Mapping):
        raise TypeError("invalid_rights_checks")

    canonical_rights: dict[str, bool] = {}
    for dimension in RIGHTS_DIMENSIONS:
        value = rights.get(dimension)
        if not isinstance(value, bool):
            raise TypeError(f"invalid_rights_{dimension}")
        canonical_rights[dimension] = value

    less_restrictive = record.get("less_restrictive_option_considered")
    if not isinstance(less_restrictive, bool):
        raise TypeError("invalid_less_restrictive_option_considered")

    human_review_required = record.get("human_review_required")
    if not isinstance(human_review_required, bool):
        raise TypeError("invalid_human_review_required")

    human_approved = record.get("human_approved")
    if not isinstance(human_approved, bool):
        raise TypeError("invalid_human_approved")

    return {
        "action": action,
        "authority_reference": _clean_text(
            record.get("authority_reference"), "authority_reference"
        ),
        "evidence_reference": _clean_text(
            record.get("evidence_reference"), "evidence_reference"
        ),
        "scope": _clean_text(record.get("scope"), "scope"),
        "duration": _clean_text(record.get("duration"), "duration", optional=True),
        "explanation_reference": _clean_text(
            record.get("explanation_reference"), "explanation_reference"
        ),
        "remedy_reference": _clean_text(
            record.get("remedy_reference"), "remedy_reference"
        ),
        "recorded_at": _instant(record.get("recorded_at"), "recorded_at"),
        "rights": canonical_rights,
        "less_restrictive_option_considered": less_restrictive,
        "human_review_required": human_review_required,
        "human_approved": human_approved,
    }


def evaluate_rights_gate(record: object) -> dict[str, Any]:
    """Return ALLOW only when all required rights controls are evidenced.

    REVIEW means execution is not authorized by this software gate. BLOCK is
    reserved for an explicit rights-control failure, such as a failed dignity,
    equality, privacy, property, accessibility, due-process, remedy,
    necessity, proportionality, or legal-authority check.
    """
    canonical = canonical_rights_record(record)
    failed = [
        dimension
        for dimension, passed in canonical["rights"].items()
        if not passed
    ]

    reasons: list[str] = []
    if failed:
        reasons.extend(f"rights_check_failed:{dimension}" for dimension in failed)
        decision = "BLOCK"
    else:
        if not canonical["less_restrictive_option_considered"]:
            reasons.append("less_restrictive_option_not_considered")
        if canonical["human_review_required"] and not canonical["human_approved"]:
            reasons.append("human_approval_missing")
        decision = "ALLOW" if not reasons else "REVIEW"

    payload = {
        **canonical,
        "decision": decision,
        "reasons": tuple(reasons),
        "human_authority_final": True,
        "automatic_confiscation_enabled": False,
        "automatic_permanent_blacklist_enabled": False,
        "legal_compliance_verified_by_software": False,
        "regulatory_authorization_inferred": False,
    }
    return {**payload, "decision_hash": _decision_hash(payload)}


def status() -> dict[str, Any]:
    return {
        "component": "SIKA Human Rights Gate",
        "rights_dimensions": RIGHTS_DIMENSIONS,
        "consequential_actions": tuple(sorted(CONSEQUENTIAL_ACTIONS)),
        "human_authority_final": True,
        "fails_closed_to_review": True,
        "automatic_confiscation_enabled": False,
        "automatic_permanent_blacklist_enabled": False,
        "legal_compliance_verified_by_software": False,
        "regulatory_authorization_inferred": False,
    }
