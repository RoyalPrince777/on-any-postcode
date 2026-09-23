"""#570 contradiction outcomes on #565's one canonical review engine."""
from dataclasses import replace
from hashlib import sha256
from uuid import UUID

import pytest

from mission_control.oap_lab_claim_edge import (
    ClaimEdge,
    ClaimEdgeBlocked,
    Source,
    admit_claim,
)
from mission_control.oap_lab_evidence_review import Challenge, challenge_claim_receipt
from mission_control.oap_lab_research import DOMAINS, MISSIONS, Notebook

OWNER = str(UUID(int=1))
CLAIM = str(UUID(int=2))
MISSION = str(UUID(int=3))
R1 = str(UUID(int=4))
R2 = str(UUID(int=5))


def admitted():
    raw1, raw2 = b"synthetic A", b"synthetic B"
    sources = tuple(
        Source(f"s{i}", raw, sha256(raw).hexdigest(),
               "2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z", f"origin{i}")
        for i, raw in enumerate((raw1, raw2), start=1)
    )
    lab = Notebook("lab-1", MISSIONS[0], DOMAINS[0], "Q", "H", "F")
    edge = ClaimEdge(
        CLAIM, MISSION, lab.identifier, lab.domain,
        "Synthetic claim", "LAB", "documents", "Synthetic record",
        "2026-01-01T00:00:00Z", owner_id=OWNER,
    )
    return admit_claim(edge, lab, sources, authenticated_owner_id=OWNER)


def reviews(a):
    return (
        Challenge(R1, "s1", a["source_sha256"][0], "supports"),
        Challenge(R2, "s2", a["source_sha256"][1], "challenges"),
    )


def run(a, items=None, **kwargs):
    return challenge_claim_receipt(
        a, reviews(a) if items is None else items,
        authenticated_reviewer_ids=frozenset({R1, R2}), **kwargs,
    )


def test_contradictions_retained_without_true_or_independent_promotion():
    a = admitted()
    result = run(a)
    assert result["has_support"] is True
    assert result["has_challenge"] is True
    assert result["contradictions_preserved"] is True
    assert result["source_independence_verified"] is False
    assert result["scientific_truth_established"] is False
    assert result["canonical_promotion_authorised"] is False
    assert result["execution_authorised"] is False
    assert result == run(a)


def test_source_swap_and_duplicate_review_rejected():
    a = admitted()
    with pytest.raises(ClaimEdgeBlocked, match="reviewer_or_source_mismatch"):
        run(a, (replace(reviews(a)[0], source_sha256="0" * 64),))
    with pytest.raises(ClaimEdgeBlocked, match="duplicate_challenge"):
        run(a, (reviews(a)[0], reviews(a)[0]))


def test_unauthenticated_reviewer_and_stop_rejected():
    a = admitted()
    with pytest.raises(ClaimEdgeBlocked, match="reviewer_or_source_mismatch"):
        run(a, (Challenge(str(UUID(int=99)), "s1", a["source_sha256"][0], "supports"),))
    with pytest.raises(ClaimEdgeBlocked, match="stop_asserted"):
        run(a, stopped=True)


def test_tampered_or_rehashed_escalated_admission_rejected():
    a = admitted()
    with pytest.raises(ClaimEdgeBlocked, match="admission_receipt_tampered"):
        run({**a, "claim_id": str(UUID(int=99))})
    altered = {**a, "execution_authorised": True}
    from json import dumps

    payload = {key: value for key, value in altered.items() if key != "receipt_sha256"}
    altered["receipt_sha256"] = sha256(
        dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    with pytest.raises(ClaimEdgeBlocked, match="review_only_admission_required"):
        run(altered)


def test_unapproved_outcome_rejected():
    with pytest.raises(ClaimEdgeBlocked, match="review_outcome_not_allowlisted"):
        Challenge(R1, "s1", "0" * 64, "proven")
