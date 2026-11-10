"""Canonical SIKA Rights Decision Record.

Builds one auditable evidence record from a SIKA Human Rights gate decision.
The record is deterministic, hash-bound and preserves the gate's truth-mode
boundaries. It does not execute the underlying financial action.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from . import sika_human_rights

RECORD_VERSION = "sika-rights-decision-record-v1"


def _canonical_json(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _hash(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


def build_decision_record(record: object) -> dict[str, Any]:
    """Evaluate the rights gate and produce one immutable decision record."""
    decision = sika_human_rights.evaluate_rights_gate(record)
    body = {
        "record_version": RECORD_VERSION,
        "action": decision["action"],
        "decision": decision["decision"],
        "reasons": tuple(decision["reasons"]),
        "authority_reference": decision["authority_reference"],
        "evidence_reference": decision["evidence_reference"],
        "scope": decision["scope"],
        "duration": decision["duration"],
        "explanation_reference": decision["explanation_reference"],
        "remedy_reference": decision["remedy_reference"],
        "recorded_at": decision["recorded_at"],
        "rights": decision["rights"],
        "less_restrictive_option_considered": decision[
            "less_restrictive_option_considered"
        ],
        "human_review_required": decision["human_review_required"],
        "human_approved": decision["human_approved"],
        "gate_decision_hash": decision["decision_hash"],
        "human_authority_final": decision["human_authority_final"],
        "automatic_confiscation_enabled": decision[
            "automatic_confiscation_enabled"
        ],
        "automatic_permanent_blacklist_enabled": decision[
            "automatic_permanent_blacklist_enabled"
        ],
        "legal_compliance_verified_by_software": decision[
            "legal_compliance_verified_by_software"
        ],
        "regulatory_authorization_inferred": decision[
            "regulatory_authorization_inferred"
        ],
        "execution_enabled": False,
    }
    return {**body, "record_hash": _hash(body)}


def verify_decision_record(record: object) -> dict[str, Any]:
    if not isinstance(record, Mapping):
        return {"verified": False, "record_hash": None}
    claimed = record.get("record_hash")
    if not isinstance(claimed, str) or len(claimed) != 64:
        return {"verified": False, "record_hash": None}
    body = {k: v for k, v in record.items() if k != "record_hash"}
    actual = _hash(body)
    gate_hash = body.get("gate_decision_hash")
    gate_hash_valid = (
        isinstance(gate_hash, str)
        and len(gate_hash) == 64
        and all(ch in "0123456789abcdef" for ch in gate_hash)
    )
    return {
        "verified": actual == claimed and gate_hash_valid,
        "record_hash": actual,
        "gate_decision_hash_valid": gate_hash_valid,
    }


def execution_gate(record: object) -> dict[str, Any]:
    """Expose bounded execution readiness without executing financial effects."""
    check = verify_decision_record(record)
    if not check["verified"] or not isinstance(record, Mapping):
        return {
            "ready": False,
            "reason": "decision_record_integrity_failed",
            "execution_enabled": False,
        }
    if record.get("decision") != "ALLOW":
        return {
            "ready": False,
            "reason": "rights_gate_not_allow",
            "execution_enabled": False,
        }
    return {
        "ready": True,
        "reason": None,
        "execution_enabled": False,
        "requires_external_authorized_executor": True,
        "human_authority_final": True,
    }


def status() -> dict[str, Any]:
    return {
        "component": "SIKA Rights Decision Record",
        "record_version": RECORD_VERSION,
        "hash_bound": True,
        "gate_hash_bound": True,
        "execution_enabled": False,
        "requires_external_authorized_executor": True,
        "human_authority_final": True,
    }
