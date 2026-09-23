"""Offline evidence corroboration and recovery negative tests."""
import json
from hashlib import sha256
from uuid import UUID

import pytest

from mission_control.oap_lab_claim_edge import ClaimEdge, ClaimEdgeBlocked, Source, admit_claim
from mission_control.oap_lab_research import DOMAINS, MISSIONS, Notebook
from mission_control.oap_lab_evidence_review import (
    CorroborationReview,
    bind_review_to_claim,
    corroboration_receipt,
    verify_recovery_chain,
)

CLAIM = str(UUID(int=11))
REVIEWER = str(UUID(int=12))
OTHER = str(UUID(int=13))


def source(index):
    raw = f"independent synthetic source {index}".encode()
    return Source(
        f"source-{index}", raw, sha256(raw).hexdigest(),
        "2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z",
        f"origin-{index}",
    )


def review(sources):
    return CorroborationReview(
        CLAIM, tuple(s.source_id for s in sources),
        tuple(s.expected_sha256 for s in sources),
        REVIEWER, "Synthetic sources reviewed; no real-world truth inferred.", True,
    )


def test_two_source_review_is_not_truth_or_authority():
    sources = (source(1), source(2))
    receipt = corroboration_receipt(
        review(sources), sources,
        authenticated_reviewer_id=REVIEWER, approved_for_review=True,
    )
    assert receipt["source_bytes_verified"] is True
    assert receipt["actual_origin_independence_proven"] is False
    assert receipt["scientific_truth_established"] is False
    assert receipt["execution_authorised"] is False
    assert len(receipt["receipt_sha256"]) == 64


def test_no_self_attested_or_wrong_reviewer():
    sources = (source(1), source(2))
    with pytest.raises(ClaimEdgeBlocked):
        corroboration_receipt(
            review(sources), sources, authenticated_reviewer_id=OTHER,
            approved_for_review=True,
        )
    with pytest.raises(ClaimEdgeBlocked):
        corroboration_receipt(
            review(sources), sources, authenticated_reviewer_id=REVIEWER,
            approved_for_review=False,
        )


def test_duplicate_and_shared_origin_fail_closed():
    sources = (source(1), source(2))
    with pytest.raises(ClaimEdgeBlocked):
        corroboration_receipt(
            review(sources), (source(1), source(1)),
            authenticated_reviewer_id=REVIEWER, approved_for_review=True,
        )
    copied = Source(
        "source-3", b"other", sha256(b"other").hexdigest(),
        "2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z", "origin-1",
    )
    with pytest.raises(ClaimEdgeBlocked):
        corroboration_receipt(
            review((source(1), copied)), (source(1), copied),
            authenticated_reviewer_id=REVIEWER, approved_for_review=True,
        )


def test_unreviewed_source_swap_is_rejected():
    originals = (source(1), source(2))
    with pytest.raises(ClaimEdgeBlocked):
        corroboration_receipt(
            review(originals), (source(1), source(3)),
            authenticated_reviewer_id=REVIEWER, approved_for_review=True,
        )


def chain():
    records = []
    previous = "GENESIS"
    for version, state in enumerate(({"step": "draft"}, {"step": "review"}), 1):
        content = {"version": version, "previous_hash": previous, "state": state}
        receipt = sha256(
            json.dumps(content, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        records.append({**content, "receipt_hash": receipt})
        previous = receipt
    return tuple(records), previous


def test_recovery_is_read_only_and_has_external_anchor():
    records, anchor = chain()
    outcome = verify_recovery_chain(records, expected_last_hash=anchor)
    assert outcome["history_integrity_verified"] is True
    assert outcome["durability_verified"] is False
    assert outcome["approval_restored"] is False
    assert outcome["execution_authorised"] is False


def test_tamper_truncation_and_reordering_rejected():
    records, anchor = chain()
    tampered = ({**records[0], "state": {"step": "approved"}}, records[1])
    for candidate in (tampered, records[:1], records[::-1]):
        with pytest.raises(ClaimEdgeBlocked):
            verify_recovery_chain(candidate, expected_last_hash=anchor)


def linked_receipts():
    sources = (source(1), source(2))
    notebook = Notebook(
        "lab-001", MISSIONS[0], DOMAINS[0], "Question?",
        "Hypothesis", "Falsification",
    )
    edge = ClaimEdge(
        claim_id=CLAIM, mission_id=str(UUID(int=14)), notebook_id="lab-001",
        domain=DOMAINS[0], claim="Synthetic claim", subject="LAB",
        relation="documents", object="Synthetic research",
        event_at="2026-01-01T00:00:00Z", owner_id=REVIEWER,
    )
    claim_receipt = admit_claim(
        edge, notebook, sources, authenticated_owner_id=REVIEWER,
    )
    review_receipt = corroboration_receipt(
        review(sources), sources,
        authenticated_reviewer_id=REVIEWER, approved_for_review=True,
    )
    return claim_receipt, review_receipt


def test_exact_handoff_is_review_only():
    claim_receipt, review_receipt = linked_receipts()
    handoff = bind_review_to_claim(claim_receipt, review_receipt)
    assert handoff["mission_id"] == claim_receipt["mission_id"]
    assert handoff["jog_memory_pointer_only"] is True
    assert handoff["durable_storage_verified"] is False
    assert handoff["independent_origin_verified"] is False
    assert handoff["scientific_truth_established"] is False
    assert handoff["execution_authorised"] is False


@pytest.mark.parametrize("field,wrong", [
    ("claim_id", str(UUID(int=99))),
    ("source_ids", ("source-1", "other-source")),
    ("source_sha256", ("0" * 64, "1" * 64)),
    ("execution_authorised", True),
])
def test_invalid_or_escalated_review_is_rejected(field, wrong):
    claim_receipt, review_receipt = linked_receipts()
    altered = {**review_receipt, field: wrong}
    with pytest.raises(ClaimEdgeBlocked):
        bind_review_to_claim(claim_receipt, altered)


def test_rehashing_a_swapped_review_does_not_bypass_exact_claim_binding():
    claim_receipt, review_receipt = linked_receipts()
    altered = {**review_receipt, "claim_id": str(UUID(int=99))}
    content = {key: val for key, val in altered.items() if key != "receipt_sha256"}
    altered["receipt_sha256"] = sha256(
        json.dumps(content, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    with pytest.raises(ClaimEdgeBlocked, match="review_claim_mismatch"):
        bind_review_to_claim(claim_receipt, altered)


def test_unverified_claim_receipt_cannot_be_promoted():
    claim_receipt, review_receipt = linked_receipts()
    altered = {**claim_receipt, "scientific_truth_established": True}
    content = {key: val for key, val in altered.items() if key != "receipt_sha256"}
    altered["receipt_sha256"] = sha256(
        json.dumps(content, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    with pytest.raises(ClaimEdgeBlocked, match="unauthorised_promotion_detected"):
        bind_review_to_claim(altered, review_receipt)
