"""Read-only PRA/FCA regulator-pack export for OAP bank readiness.

The pack is derived from the durable append-only evidence store. It creates a
canonical snapshot and SHA-256 digest so reviewers can detect changes. It does
not digitally sign the pack and does not imply regulator approval.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from . import bank_authorisation, bank_authorisation_store

PACK_VERSION = "oap_bank_regulator_pack_v1"


def _canonical_payload(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def build_pack() -> dict[str, Any]:
    register = bank_authorisation_store.latest_register()
    readiness = bank_authorisation.readiness_status(evidence=register)

    accepted = []
    in_review = []
    rejected = []
    missing = []

    for category in bank_authorisation.PRA_FCA_EVIDENCE:
        item = dict(register.get(category) or {})
        status = str(item.get("status") or "MISSING").upper()
        row = {
            "category": category,
            "status": status,
            "evidence_reference": item.get("evidence_reference"),
            "reviewed_by": item.get("reviewed_by"),
            "recorded_at": item.get("recorded_at"),
        }
        if status == "ACCEPTED":
            accepted.append(row)
        elif status in {"DRAFT", "REVIEWED"}:
            in_review.append(row)
        elif status == "REJECTED":
            rejected.append(row)
        else:
            missing.append(row)

    body = {
        "pack_version": PACK_VERSION,
        "institution": readiness["institution"],
        "parent": readiness["parent"],
        "jurisdiction": readiness["jurisdiction"],
        "authorisation_route": readiness["route"],
        "evidence_total": readiness["evidence_total"],
        "evidence_accepted": len(accepted),
        "evidence_in_review": len(in_review),
        "evidence_rejected": len(rejected),
        "evidence_missing": len(missing),
        "accepted": accepted,
        "in_review": in_review,
        "rejected": rejected,
        "missing": missing,
        "application_ready": readiness["application_ready"],
        "authorised_bank": readiness["authorised_bank"],
        "deposit_taking_enabled": readiness["deposit_taking_enabled"],
        "regulated_execution_enabled": readiness["regulated_execution_enabled"],
        "regulator_authorisation_granted": readiness["authorised_bank"],
        "digital_signature_present": False,
        "humanitarian_or_human_rights_purpose_bypasses_authorisation": False,
        "human_authority_final": True,
    }

    digest = hashlib.sha256(_canonical_payload(body).encode("utf-8")).hexdigest()
    return {
        **body,
        "digest_algorithm": "SHA-256",
        "pack_digest": digest,
    }


def verify_pack_digest(pack: dict[str, Any]) -> bool:
    supplied = str(pack.get("pack_digest") or "")
    body = {
        key: value
        for key, value in pack.items()
        if key not in {"pack_digest", "digest_algorithm"}
    }
    expected = hashlib.sha256(_canonical_payload(body).encode("utf-8")).hexdigest()
    return bool(supplied) and supplied == expected
