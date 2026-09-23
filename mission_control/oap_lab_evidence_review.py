"""OAP LAB offline corroboration and recovery review; never a truth or action gate.

No persistence, API, source fetching, memory promotion, clinical decisions or
consequential execution. Extend the canonical LAB Claim Edge, not the graph.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256

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
        if not isinstance(self.rationale, str) or not self.rationale.strip() or len(self.rationale) > 1024:
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
        if (type(record.get("version")) is not int
                or record["version"] != index
                or record.get("previous_hash") != previous):
            raise ClaimEdgeBlocked("recovery_history_break")
        state = record.get("state")
        if not isinstance(state, Mapping) or not state:
            raise ClaimEdgeBlocked("recovery_state_required")
        try:
            canonical = json.dumps(
                {"version": index, "previous_hash": previous, "state": state},
                sort_keys=True, separators=(",", ":"), allow_nan=False,
            )
        except (TypeError, ValueError, OverflowError) as exc:
            raise ClaimEdgeBlocked("invalid_recovery_state_encoding") from exc
        expected = sha256(canonical.encode()).hexdigest()
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


def bind_review_to_claim(
    claim_receipt: Mapping[str, object],
    review_receipt: Mapping[str, object],
) -> dict[str, object]:
    """Reconcile exact, unmodified read-only receipts; never restore authority.

    Caller authentication and persistent storage are owned by existing systems.
    Receipts are integrity evidence, NOT cryptographic signatures or proof of truth.
    """
    if not isinstance(claim_receipt, Mapping) or not isinstance(review_receipt, Mapping):
        raise ClaimEdgeBlocked("typed_receipts_required")
    for receipt in (claim_receipt, review_receipt):
        digest = receipt.get("receipt_sha256")
        if not isinstance(digest, str) or len(digest) != 64:
            raise ClaimEdgeBlocked("receipt_hash_required")
        payload = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
        try:
            verified = sha256(
                json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
            ).hexdigest()
        except (TypeError, ValueError) as exc:
            raise ClaimEdgeBlocked("invalid_receipt_content") from exc
        if digest != verified:
            raise ClaimEdgeBlocked("receipt_tampered")
    if claim_receipt.get("claim_id") != review_receipt.get("claim_id"):
        raise ClaimEdgeBlocked("review_claim_mismatch")
    if claim_receipt.get("source_ids") != list(review_receipt.get("source_ids", ())):
        raise ClaimEdgeBlocked("review_source_ids_mismatch")
    if claim_receipt.get("source_sha256") != list(review_receipt.get("source_sha256", ())):
        raise ClaimEdgeBlocked("review_source_bytes_mismatch")
    if (claim_receipt.get("review_only") is not True
            or review_receipt.get("human_review_attested") is not True):
        raise ClaimEdgeBlocked("review_only_attestation_required")
    if any(receipt.get(flag) is not False for receipt in (claim_receipt, review_receipt)
           for flag in ("scientific_truth_established", "canonical_promotion_authorised",
                        "publication_authorised", "execution_authorised")):
        raise ClaimEdgeBlocked("unauthorised_promotion_detected")
    return {
        "claim_id": claim_receipt["claim_id"],
        "mission_id": claim_receipt["mission_id"],
        "notebook_id": claim_receipt["notebook_id"],
        "claim_receipt_sha256": claim_receipt["receipt_sha256"],
        "review_receipt_sha256": review_receipt["receipt_sha256"],
        "handoff": "read_only_research_review",
        "jog_memory_pointer_only": True,
        "durable_storage_verified": False,
        "independent_origin_verified": False,
        "scientific_truth_established": False,
        "canonical_promotion_authorised": False,
        "publication_authorised": False,
        "execution_authorised": False,
    }


@dataclass(frozen=True)
class Challenge:
    """Reviewer-specific finding; no inferred source independence or truth."""
    reviewer_id: str
    source_id: str
    source_sha256: str
    outcome: str

    def __post_init__(self) -> None:
        from uuid import UUID

        try:
            UUID(self.reviewer_id)
        except (TypeError, ValueError, AttributeError) as exc:
            raise ClaimEdgeBlocked("canonical_reviewer_id_required") from exc
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise ClaimEdgeBlocked("reviewed_source_id_required")
        if not isinstance(self.source_sha256, str) or (
            len(self.source_sha256) != 64
            or any(char not in "0123456789abcdef" for char in self.source_sha256)
        ):
            raise ClaimEdgeBlocked("reviewed_source_digest_required")
        if self.outcome not in ("supports", "challenges", "inconclusive"):
            raise ClaimEdgeBlocked("review_outcome_not_allowlisted")


def challenge_claim_receipt(
    admitted: Mapping[str, object],
    challenges: tuple[Challenge, ...],
    *,
    authenticated_reviewer_ids: frozenset[str],
    stopped: bool = False,
) -> dict[str, object]:
    """Port #570's unique contradiction review onto #565's canonical contract.

    Never duplicate recovery, persist evidence, authenticate independent
    source origins, or promote synthetic research to scientific truth.
    """
    from uuid import UUID

    if stopped:
        raise ClaimEdgeBlocked("stop_asserted")
    if not isinstance(admitted, Mapping):
        raise ClaimEdgeBlocked("verified_admission_required")
    digest = admitted.get("receipt_sha256")
    payload = {key: value for key, value in admitted.items() if key != "receipt_sha256"}
    try:
        expected = sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        ).hexdigest()
    except (TypeError, ValueError) as exc:
        raise ClaimEdgeBlocked("invalid_admission_receipt") from exc
    if not isinstance(digest, str) or digest != expected:
        raise ClaimEdgeBlocked("admission_receipt_tampered")
    if admitted.get("review_only") is not True or any(
        admitted.get(key) is not False for key in (
            "independence_verified", "scientific_truth_established",
            "canonical_promotion_authorised", "publication_authorised",
            "execution_authorised",
        )
    ):
        raise ClaimEdgeBlocked("review_only_admission_required")
    source_ids = admitted.get("source_ids")
    source_hashes = admitted.get("source_sha256")
    if not isinstance(source_ids, list) or not isinstance(source_hashes, list):
        raise ClaimEdgeBlocked("verified_sources_required")
    if not source_ids or len(source_ids) != len(source_hashes) or len(set(source_ids)) != len(source_ids):
        raise ClaimEdgeBlocked("invalid_admitted_source_links")
    sources = dict(zip(source_ids, source_hashes, strict=True))
    if not isinstance(challenges, tuple) or not challenges or any(
        not isinstance(item, Challenge) for item in challenges
    ):
        raise ClaimEdgeBlocked("typed_challenge_required")
    try:
        reviewers = {str(UUID(x)) for x in authenticated_reviewer_ids}
    except (TypeError, ValueError, AttributeError) as exc:
        raise ClaimEdgeBlocked("authenticated_reviewers_required") from exc
    if any(
        str(UUID(item.reviewer_id)) not in reviewers
        or sources.get(item.source_id) != item.source_sha256
        for item in challenges
    ):
        raise ClaimEdgeBlocked("reviewer_or_source_mismatch")
    if len({(item.reviewer_id, item.source_id) for item in challenges}) != len(challenges):
        raise ClaimEdgeBlocked("duplicate_challenge")
    outcomes = {item.outcome for item in challenges}
    result = {
        "claim_id": admitted["claim_id"],
        "admission_receipt_sha256": digest,
        "reviewer_count": len({item.reviewer_id for item in challenges}),
        "reviewed_source_count": len({item.source_id for item in challenges}),
        "has_support": "supports" in outcomes,
        "has_challenge": "challenges" in outcomes,
        "has_inconclusive": "inconclusive" in outcomes,
        "contradictions_preserved": True,
        "source_independence_verified": False,
        "scientific_truth_established": False,
        "canonical_promotion_authorised": False,
        "publication_authorised": False,
        "execution_authorised": False,
        "review_only": True,
    }
    result["receipt_sha256"] = sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return result
