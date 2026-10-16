"""Pressure tests for Koradaso human claim review."""
import inspect

from mission_control import koradaso_reviews, koradaso_schema

SOURCE = inspect.getsource(koradaso_reviews)
SCHEMA = "\n".join(koradaso_schema.STATEMENTS)

def test_review_permission_registered_but_not_auto_granted():
    assert koradaso_reviews.REVIEW_PERMISSION in SCHEMA
    assert "INSERT INTO oap_role_permissions" not in SCHEMA

def test_stronger_truth_states_require_evidence():
    for state in ("DOCUMENTED", "SCHOLARLY", "FAMILY_CONFIRMED", "ORAL_TRADITION"):
        assert state in koradaso_reviews.EVIDENCE_REQUIRED
    assert "review_evidence_required" in SOURCE

def test_documented_requires_support_and_rejects_known_contradiction():
    assert "documented_supporting_evidence_required" in SOURCE
    assert "documented_claim_has_contradictory_evidence" in SOURCE
    assert '"CONTRADICTS"' in SOURCE

def test_review_is_audited_before_commit_and_never_grants_royal_status():
    audit = SOURCE.index("KORADASO_CLAIM_REVIEWED")
    commit = SOURCE.index("connection.commit()", audit)
    assert audit < commit
    assert '"royal_status_granted": False' in SOURCE
