"""Private film evidence-to-claim reconciliation: never a rights approval.

Compares a locally byte-checked submission against the SAME candidate, country,
model and bounded licence window. Missing, mismatched or stale inputs invalidate
the review envelope. All outcomes remain non-authorising until an independent
first-party rights authority and Founder release decision exist.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import date

from . import open_cinema_byte_integrity as byte_integrity
from . import open_cinema_evidence as evidence_contract


def reconcile(
    candidate_id: object,
    territory: object,
    evidence: object,
    document: object,
    *,
    today: object,
) -> dict[str, object]:
    """Pure bounded receipt, no storage, filesystem, network or playback."""
    review = evidence_contract.review_envelope(candidate_id, territory, [evidence])
    bytes_result = byte_integrity.check_bytes(evidence, document)
    refs = review["submitted_evidence"]
    ref = refs[0] if refs else None
    linked = bool(
        ref and ref["evidence_id"] == bytes_result["evidence_id"]
        and ref["submitted_sha256"] == (
            evidence.get("sha256") if isinstance(evidence, Mapping) else None
        )
    )
    try:
        checked_today = date.fromisoformat(today) if (
            isinstance(today, str) and len(today) == 10
        ) else None
    except ValueError:
        checked_today = None
    window = bool(
        checked_today and review["starts_on"] and review["ends_on"]
        and date.fromisoformat(review["starts_on"])
        <= checked_today <= date.fromisoformat(review["ends_on"])
    )
    # The submitted evidence must identify the exact claim it accompanies.
    # These fields are still untrusted applicant statements, not source attestation.
    submitted = evidence if isinstance(evidence, Mapping) else {}
    bound = bool(
        review["candidate_id"] and review["country"] and review["models"]
        and submitted.get("candidate_id") == review["candidate_id"]
        and submitted.get("country") == review["country"]
        and type(submitted.get("models")) is list
        and len(submitted["models"]) == len(review["models"])
        and sorted(submitted["models"]) == review["models"]
        and submitted.get("starts_on") == review["starts_on"]
        and submitted.get("ends_on") == review["ends_on"]
    )
    receipt_valid = bool(
        review["candidate_id"] and review["country"] and review["models"]
        and bound and linked and bytes_result["digest_match"] and window
    )
    blockers = list(review["blockers"])
    if not bound:
        blockers.append("evidence_not_bound_to_exact_candidate_country_models_window")
    if not linked:
        blockers.append("evidence_reference_mismatch_or_missing")
    if not bytes_result["digest_match"]:
        blockers.append("evidence_bytes_mismatch_or_missing")
    if not window:
        blockers.append("territory_window_expired_or_invalid")
    return {
        "candidate_id": review["candidate_id"],
        "country": review["country"],
        "models": review["models"],
        "evidence_id": ref["evidence_id"] if ref else None,
        "claim_binding_matches_submission": bound,
        "local_digest_matches_submission": bool(
            linked and bytes_result["digest_match"]
        ),
        "claimed_window_current": window,
        "private_review_receipt_complete": receipt_valid,
        "independent_source_attested": False,
        "licensor_authority_verified": False,
        "chain_of_title_verified": False,
        "country_rights_verified": False,
        "licence_acquired": False,
        "publication_enabled": False,
        "playback_enabled": False,
        "recovery": "resubmit_evidence_and_repeat_independent_review"
        if not receipt_valid else "await_independent_rights_authority",
        "blockers": blockers,
        "human_authority_final": True,
    }
