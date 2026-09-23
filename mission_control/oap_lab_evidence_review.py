"""Review-only evidence challenge and deterministic recovery for OAP LAB.

Pure functions consume authenticated caller context; never create a second graph,
HRM store, identity authority, scientific truth certification, or deployment path.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from mission_control.oap_lab_claim_edge import ClaimEdgeBlocked


def _hash(record: dict[str, Any]) -> str:
    return sha256(
        json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


@dataclass(frozen=True)
class Review:
    reviewer_id: str
    source_id: str
    source_sha256: str
    outcome: str

    def __post_init__(self) -> None:
        if not self.reviewer_id or not self.source_id:
            raise ClaimEdgeBlocked("reviewer_and_source_required")
        if self.outcome not in ("supports", "challenges", "inconclusive"):
            raise ClaimEdgeBlocked("review_outcome_not_allowlisted")
        if (
            len(self.source_sha256) != 64
            or any(c not in "0123456789abcdef" for c in self.source_sha256)
        ):
            raise ClaimEdgeBlocked("review_source_hash_invalid")


def challenge_evidence(
    admitted: dict[str, Any],
    reviews: tuple[Review, ...],
    *,
    authenticated_reviewer_ids: frozenset[str],
    stopped: bool = False,
) -> dict[str, Any]:
    """Assess traceability; independent review never automatically proves truth."""
    if stopped:
        raise ClaimEdgeBlocked("stop_asserted")
    if admitted.get("review_only") is not True or admitted.get(
        "canonical_promotion_authorised"
    ) is not False:
        raise ClaimEdgeBlocked("review_only_admission_required")
    if admitted.get("receipt_sha256") != _hash(
        {key: value for key, value in admitted.items() if key != "receipt_sha256"}
    ):
        raise ClaimEdgeBlocked("admission_receipt_tampered")
    sources = dict(zip(
        admitted["source_ids"], admitted["source_sha256"], strict=True
    ))
    if not reviews or any(not isinstance(item, Review) for item in reviews):
        raise ClaimEdgeBlocked("typed_review_required")
    if any(
        item.reviewer_id not in authenticated_reviewer_ids
        or sources.get(item.source_id) != item.source_sha256
        for item in reviews
    ):
        raise ClaimEdgeBlocked("reviewer_or_source_mismatch")
    if len({(item.reviewer_id, item.source_id) for item in reviews}) != len(reviews):
        raise ClaimEdgeBlocked("duplicate_review")
    reviewers = {item.reviewer_id for item in reviews}
    outcomes = {item.outcome for item in reviews}
    result = {
        "claim_id": admitted["claim_id"],
        "admission_receipt": admitted["receipt_sha256"],
        "reviewer_count": len(reviewers),
        "reviewed_source_count": len({item.source_id for item in reviews}),
        "has_challenge": "challenges" in outcomes,
        "has_support": "supports" in outcomes,
        "contradictions_preserved": True,
        "independent_origins_claimed": admitted["independent_origins_claimed"],
        "source_independence_verified": False,
        "scientific_truth_established": False,
        "canonical_promotion_authorised": False,
        "publication_authorised": False,
        "execution_authorised": False,
        "review_only": True,
    }
    return {**result, "receipt_sha256": _hash(result)}


def append_recovery(
    history: tuple[dict[str, Any], ...],
    review_receipt: dict[str, Any],
    *,
    stopped: bool = False,
) -> tuple[dict[str, Any], ...]:
    """Immutable local revision chain; caller must provide governed durable store."""
    if stopped:
        raise ClaimEdgeBlocked("stop_asserted")
    previous = "GENESIS"
    for number, entry in enumerate(history, start=1):
        record = {key: value for key, value in entry.items() if key != "receipt_sha256"}
        if (
            record.get("version") != number
            or record.get("previous") != previous
            or entry.get("receipt_sha256") != _hash(record)
        ):
            raise ClaimEdgeBlocked("recovery_history_integrity_failed")
        previous = entry["receipt_sha256"]
    if review_receipt.get("receipt_sha256") != _hash({
        key: value for key, value in review_receipt.items()
        if key != "receipt_sha256"
    }) or review_receipt.get("review_only") is not True:
        raise ClaimEdgeBlocked("invalid_review_receipt")
    entry = {
        "version": len(history) + 1,
        "previous": previous,
        "review_receipt": review_receipt["receipt_sha256"],
        "claim_id": review_receipt["claim_id"],
        "resume_mode": "review_only",
        "durable_persistence_verified": False,
        "execution_authorised": False,
    }
    return (*history, {**entry, "receipt_sha256": _hash(entry)})
