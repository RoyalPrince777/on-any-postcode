"""Pressure-test Koradaso public projection boundaries."""
import inspect

from mission_control import koradaso_publications, koradaso_schema

SOURCE = inspect.getsource(koradaso_publications)
SCHEMA = "\n".join(koradaso_schema.STATEMENTS)

def test_publication_permission_is_separate_and_not_auto_granted():
    assert koradaso_publications.PUBLISH_PERMISSION in SCHEMA
    assert koradaso_publications.PUBLISH_PERMISSION != "KORADASO_REVIEW_CLAIMS"
    assert "INSERT INTO oap_role_permissions" not in SCHEMA

def test_publication_requires_prior_human_review():
    assert "human_review_required_before_publication" in SOURCE
    assert "koradaso_claim_reviews" in SOURCE

def test_public_projection_does_not_read_private_evidence_payload():
    assert "koradaso_evidence" not in SOURCE
    assert "source_uri" not in SOURCE
    assert "original_hash" not in SOURCE
    assert "public_summary" in SOURCE

def test_publication_and_revocation_are_audited_before_commit():
    assert "KORADASO_HERITAGE_PUBLISHED" in SOURCE
    assert "KORADASO_HERITAGE_REVOKED" in SOURCE
    assert SOURCE.count("connection.commit()") == 2

def test_revocation_preserves_record():
    assert "revoked_at=CURRENT_TIMESTAMP" in SOURCE
    assert "DELETE FROM koradaso_publications" not in SOURCE
