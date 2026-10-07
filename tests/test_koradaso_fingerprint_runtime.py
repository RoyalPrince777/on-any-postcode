"""Executable reviewed-claim fingerprint regression tests.

No external database is required for these deterministic contract checks.
Real PostgreSQL transaction proof remains a separate Gate-25 requirement.
"""
from __future__ import annotations

from uuid import UUID

from mission_control.koradaso_consent import claim_fingerprint

CLAIM = UUID("00000000-0000-0000-0000-000000000001")


class ReviewedClaimConnection:
    def __init__(self):
        self.claim = ("PERSON", "ancestor", "relation", "recorded", "DOCUMENTED", 0.8, "ME", CLAIM)
        self.reviews = [(UUID("00000000-0000-0000-0000-000000000002"), "RESEARCHING", "DOCUMENTED", "reviewed", CLAIM)]
        self.evidence = [(UUID("00000000-0000-0000-0000-000000000003"), "SUPPORTS", "original", "ME")]
        self.versions = [(UUID("00000000-0000-0000-0000-000000000003"), 1, "content", "ORIGINAL")]
        self._result = None

    def execute(self, sql, params):
        assert params == (CLAIM,)
        if "FROM koradaso_claims" in sql:
            self._result = self.claim
        elif "FROM koradaso_claim_reviews" in sql:
            self._result = self.reviews
        elif "FROM koradaso_claim_evidence ce" in sql:
            self._result = self.evidence
        elif "FROM koradaso_evidence_versions v" in sql:
            self._result = self.versions
        else:
            raise AssertionError(f"Unexpected query: {sql}")
        return self

    def fetchone(self):
        return self._result

    def fetchall(self):
        return self._result


def test_claim_fingerprint_stable_when_reviewed_state_unchanged():
    connection = ReviewedClaimConnection()
    assert claim_fingerprint(connection, CLAIM) == claim_fingerprint(connection, CLAIM)


def test_claim_fingerprint_invalidated_by_claim_change():
    connection = ReviewedClaimConnection()
    before = claim_fingerprint(connection, CLAIM)
    connection.claim = (*connection.claim[:3], "changed", *connection.claim[4:])
    assert claim_fingerprint(connection, CLAIM) != before


def test_claim_fingerprint_invalidated_by_new_review():
    connection = ReviewedClaimConnection()
    before = claim_fingerprint(connection, CLAIM)
    connection.reviews.append((UUID("00000000-0000-0000-0000-000000000004"), "DOCUMENTED", "CONTESTED", "challenged", CLAIM))
    assert claim_fingerprint(connection, CLAIM) != before


def test_claim_fingerprint_invalidated_by_evidence_version():
    connection = ReviewedClaimConnection()
    before = claim_fingerprint(connection, CLAIM)
    connection.versions.append((connection.versions[0][0], 2, "corrected", "CORRECTION"))
    assert claim_fingerprint(connection, CLAIM) != before


def test_claim_fingerprint_fails_closed_without_review():
    connection = ReviewedClaimConnection()
    connection.reviews = []
    try:
        claim_fingerprint(connection, CLAIM)
    except ValueError as exc:
        assert str(exc) == "human_review_required_before_release"
    else:
        raise AssertionError("unreviewed claim fingerprint unexpectedly permitted")
