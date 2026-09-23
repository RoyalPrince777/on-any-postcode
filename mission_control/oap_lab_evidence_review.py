"""OAP LAB offline corroboration and recovery review; never a truth or action gate.

No persistence, API, source fetching, memory promotion, clinical decisions or
consequential execution. Extend the canonical LAB Claim Edge, not the graph.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from typing import Mapping

from mission_control.oap_lab_claim_edge import ClaimEdgeBlocked, Source


@dataclass(frozen=True)
class CorroborationReview:
    claim_id: str
    source_ids: tuple[str, ...]
    source_sha256: tuple[str, ...]
    reviewer_id: str
    rationale: str
    independently_reviewed: bool = False

    def __post_init__(self) -> None:
        from uuid import UUID

        try:
            UUID(self.claim_id)
            UUID(self.reviewer_id)
        except (TypeError, ValueError, AttributeError) as exc:
            raise ClaimEdgeBlocked("valid_claim_and_reviewer_ids_required") from exc
        if not self.rationale.strip() or len(self.rationale) > 1024:
            raise ClaimEdgeBlocked("bounded_review_rationale_required")
        if len(self.source_ids) != len(self.source_sha256) or len(self.source_ids) < 2:
            raise ClaimEdgeBlocked("two_evidence_references_required")


def corroboration_receipt(
    review: CorroborationReview,
    sources: tuple[Source, ...],
    *,
    authenticated_reviewer_id: str,
    approved_for_review: bool,
) -> dict[str, object]:
    """Check the exact reviewed bytes and metadata; do not claim independent truth."""
    from uuid import UUID

    if not isinstance(review, CorroborationReview):
        raise ClaimEdgeBlocked("typed_review_required")
    try:
        if UUID(authenticated_reviewer_id) != UUID(review.reviewer_id):
            raise ClaimEdgeBlocked("reviewer_identity_mismatch")
    except (TypeError, ValueError, AttributeError) as exc:
        raise ClaimEdgeBlocked("reviewer_identity_mismatch") from exc
    if not approved_for_review or review.independently_reviewed is not True:
        raise ClaimEdgeBlocked("explicit_review_attestation_required")
    if not isinstance(sources, tuple) or len(sources) < 2 or any(
        not isinstance(source, Source) for source in sources
    ):
        raise ClaimEdgeBlocked("two_valid_sources_required")
    if len({source.source_id for source in sources}) != len(sources):
        raise ClaimEdgeBlocked("duplicate_source_ids")
    if len({source.expected_sha256 for source in sources}) != len(sources):
        raise ClaimEdgeBlocked("duplicated_source_bytes")
    if len({source.independent_origin for source in sources}) != len(sources):
        raise ClaimEdgeBlocked("shared_claimed_origin")
    if tuple(source.source_id for source in sources) != review.source_ids:
        raise ClaimEdgeBlocked("reviewed_source_ids_mismatch")
    if tuple(source.expected_sha256 for source in sources) != review.source_sha256:
        raise ClaimEdgeBlocked("reviewed_source_hash_mismatch")
    payload = {
        "claim_id": review.claim_id,
        "reviewer_id": review.reviewer_id,
        "source_ids": review.source_ids,
        "source_sha256": review.source_sha256,
        "review_rationale_sha256": sha256(review.rationale.encode()).hexdigest(),
        "source_bytes_verified": True,
        "distinct_claimed_origins": True,
        "human_review_attested": True,
        "actual_origin_independence_proven": False,
        "scientific_truth_established": False,
        "canonical_promotion_authorised": False,
        "publication_authorised": False,
        "execution_authorised": False,
    }
    payload["receipt_sha256"] = sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return payload


def verify_recovery_chain(
    records: tuple[Mapping[str, object], ...],
    *,
    expected_last_hash: str,
) -> dict[str, object]:
    """Read-only integrity review of supplied versions; does not claim durable storage."""
    if not records or not isinstance(records, tuple):
        raise ClaimEdgeBlocked("recovery_records_required")
    previous = "GENESIS"
    for index, record in enumerate(records, start=1):
        if not isinstance(record, Mapping):
            raise ClaimEdgeBlocked("invalid_recovery_record")
        if record.get("version") != index or record.get("previous_hash") != previous:
            raise ClaimEdgeBlocked("recovery_history_break")
        state = record.get("state")
        if not isinstance(state, Mapping) or not state:
            raise ClaimEdgeBlocked("recovery_state_required")
        expected = sha256(
            json.dumps(
                {"version": index, "previous_hash": previous, "state": state},
                sort_keys=True, separators=(",", ":"), allow_nan=False,
            ).encode()
        ).hexdigest()
        if record.get("receipt_hash") != expected:
            raise ClaimEdgeBlocked("recovery_hash_mismatch")
        previous = expected
    if expected_last_hash != previous:
        raise ClaimEdgeBlocked("recovery_anchor_mismatch")
    return {
        "history_integrity_verified": True,
        "version_count": len(records),
        "last_hash": previous,
        "resume_mode": "review_only",
        "durability_verified": False,
        "approval_restored": False,
        "execution_authorised": False,
    }
