"""Negative tests for read-only OAP LAB review and recovery contracts."""
from hashlib import sha256
from uuid import UUID

import pytest

from mission_control.oap_lab_claim_edge import (
    ClaimEdge,
    ClaimEdgeBlocked,
    Source,
    admit_claim,
)
from mission_control.oap_lab_evidence_review import (
    Review,
    append_recovery,
    challenge_evidence,
)
from mission_control.oap_lab_research import DOMAINS, MISSIONS, Notebook

OWNER = str(UUID(int=1))
CLAIM = str(UUID(int=2))
MISSION = str(UUID(int=3))


def admitted(mission=MISSIONS[0], domain=DOMAINS[0]):
    text = b"synthetic evidence without personal data"
    record = Source(
        "s1", text, sha256(text).hexdigest(),
        "2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z", "original-1",
    )
    notebook = Notebook("lab-1", mission, domain, "Q", "H", "F")
    edge = ClaimEdge(
        CLAIM, MISSION, notebook.identifier, domain,
        "Synthetic claim", "Research", "documents", "Record",
        "2026-01-01T00:00:00Z", owner_id=OWNER,
    )
    return admit_claim(edge, notebook, (record,), authenticated_owner_id=OWNER)


def reviewed(admission):
    review = Review("reviewer-1", "s1", admission["source_sha256"][0], "challenges")
    return challenge_evidence(
        admission, (review,), authenticated_reviewer_ids=frozenset({"reviewer-1"})
    )


@pytest.mark.parametrize("mission", MISSIONS)
def test_eight_missions_keep_review_only(mission):
    result = reviewed(admitted(mission))
    assert result["scientific_truth_established"] is False
    assert result["has_challenge"] is True


@pytest.mark.parametrize("domain", DOMAINS)
def test_twenty_one_domains_keep_review_only(domain):
    result = reviewed(admitted(domain=domain))
    assert result["canonical_promotion_authorised"] is False


def test_review_source_tampering_and_wrong_reviewer_fail():
    record = admitted()
    for bad in (
        Review("reviewer-1", "s1", "0" * 64, "supports"),
        Review("unknown", "s1", record["source_sha256"][0], "supports"),
    ):
        with pytest.raises(ClaimEdgeBlocked):
            challenge_evidence(
                record, (bad,), authenticated_reviewer_ids=frozenset({"reviewer-1"})
            )


def test_duplicate_review_and_fake_admission_fail():
    record = admitted()
    review = Review("reviewer-1", "s1", record["source_sha256"][0], "supports")
    with pytest.raises(ClaimEdgeBlocked, match="duplicate_review"):
        challenge_evidence(
            record, (review, review),
            authenticated_reviewer_ids=frozenset({"reviewer-1"}),
        )
    with pytest.raises(ClaimEdgeBlocked, match="admission_receipt_tampered"):
        challenge_evidence(
            {**record, "classification": "established"},
            (review,), authenticated_reviewer_ids=frozenset({"reviewer-1"}),
        )


def test_review_stop_and_fake_truth_promotion_fail():
    record = admitted()
    review = Review("reviewer-1", "s1", record["source_sha256"][0], "supports")
    with pytest.raises(ClaimEdgeBlocked, match="stop_asserted"):
        challenge_evidence(
            record, (review,),
            authenticated_reviewer_ids=frozenset({"reviewer-1"}), stopped=True,
        )
    assert challenge_evidence(
        record, (review,), authenticated_reviewer_ids=frozenset({"reviewer-1"}),
    )["source_independence_verified"] is False


def test_recovery_chain_is_deterministic_and_fails_closed():
    review = reviewed(admitted())
    one = append_recovery((), review)
    two = append_recovery(one, review)
    assert two == append_recovery(one, review)
    assert two[-1]["version"] == 2
    assert two[-1]["resume_mode"] == "review_only"
    assert two[-1]["durable_persistence_verified"] is False
    with pytest.raises(ClaimEdgeBlocked, match="recovery_history_integrity_failed"):
        append_recovery((dict(one[0], previous="altered"),), review)
    with pytest.raises(ClaimEdgeBlocked, match="invalid_review_receipt"):
        append_recovery(one, dict(review, execution_authorised=True))
    with pytest.raises(ClaimEdgeBlocked, match="stop_asserted"):
        append_recovery(one, review, stopped=True)
