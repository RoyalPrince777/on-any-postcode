"""First-party OAP humanitarian finding verification; no external approval dependency.

Independent verification means SMI assesses evidence, not that it invents it.
No automatic publication, emergency dispatch, or external data transmission.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

ALLOWED_EVIDENCE_KINDS = frozenset(("first_party_observation", "first_party_measurement", "first_party_document", "external_reference"))
MIN_INDEPENDENT_EVIDENCE = 2


def verify_original_finding(finding: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate one OAP-authored finding and fail closed on missing evidence.

    The resulting status is an internal assessment, never an official alert or
    a substitute for an authorised human decision. No personal data is copied.
    """
    finding_id = str(finding.get("id") or "").strip()[:120]
    claim = str(finding.get("claim") or "").strip()
    raw_evidence = finding.get("evidence")
    evidence = raw_evidence if isinstance(raw_evidence, (list, tuple)) else ()
    accepted: set[str] = set()
    ids: set[str] = set()
    for item in evidence[:50]:
        if not isinstance(item, Mapping):
            continue
        evidence_id = str(item.get("id") or "").strip()
        kind = str(item.get("kind") or "")
        if not evidence_id or evidence_id in ids or kind not in ALLOWED_EVIDENCE_KINDS:
            continue
        if item.get("reviewed") is not True or item.get("supports_claim") is not True:
            continue
        ids.add(evidence_id)
        accepted.add(kind)
    # External reports can corroborate an OAP finding, but cannot alone establish
    # that the finding rests on OAP's own original evidence.
    first_party_evidence = bool(accepted - {"external_reference"})
    independent = len(ids) >= MIN_INDEPENDENT_EVIDENCE and first_party_evidence
    original = bool(finding_id and claim and finding.get("authored_by") == "OAP")
    human_review = finding.get("human_reviewed") is True
    status = "internally_verified" if original and independent and human_review else "unconfirmed"
    return {
        "id": finding_id,
        "origin": "OAP" if original else "unestablished",
        "status": status,
        "accepted_evidence_count": len(ids),
        "evidence_kinds": tuple(sorted(accepted)),
        "human_reviewed": human_review,
        "external_approval_required": False,
        "official_emergency_alert": False,
        "public_release_authorised": False,
        "autonomous_dispatch_authorised": False,
        "checked_at": datetime.now(UTC).isoformat(),
    }


def first_party_verification_state() -> dict[str, Any]:
    """Readiness only; do not invent or report verified findings."""
    return {
        "owner": "OAP",
        "verifier": "SMI",
        "original_finding_contract_available": True,
        "verified_findings": 0,
        "public_release_authorised": False,
        "external_approval_required": False,
        "human_authority_final": True,
    }
