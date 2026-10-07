"""KORADASO Gate-25 consent binding regression tests.

These are source/algorithm tests, not substitutes for PostgreSQL integration.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "mission_control"


def test_release_requires_exact_summary_and_reviewed_claim_fingerprint():
    source = (ROOT / "koradaso_releases.py").read_text()
    assert "release_public_summary_required" in source
    assert "sha256(summary.encode()).hexdigest()" in source
    assert "claim_fingerprint(connection, claim)" in source
    assert "claim_creator_release_consent_required" in source


def test_publication_checks_both_consent_fingerprints():
    source = (ROOT / "koradaso_publications.py").read_text()
    assert "summary_hash=%s" in source
    assert "claim_fingerprint=%s" in source
    assert "claim_fingerprint(connection, claim)" in source
    assert "revoked_at IS NULL" in source
    assert sha256("approved".encode()).hexdigest() != sha256("altered".encode()).hexdigest()


def test_withdrawal_uses_same_claim_first_lock_as_publication():
    release = (ROOT / "koradaso_releases.py").read_text()
    publication = (ROOT / "koradaso_publications.py").read_text()
    revoke = release.split("def revoke_release(", 1)[1]
    assert revoke.index("FROM koradaso_claims WHERE claim_id=%s FOR UPDATE") < revoke.index(
        "WHERE release_id=%s FOR UPDATE"
    )
    assert "FROM koradaso_claims WHERE claim_id=%s FOR UPDATE" in publication
    assert "release_owner_required_for_revocation" in revoke
    assert "UPDATE koradaso_publications" in revoke


def test_legacy_consents_without_fingerprints_fail_closed():
    schema = (ROOT / "koradaso_schema.py").read_text()
    assert "ADD COLUMN IF NOT EXISTS summary_hash TEXT" in schema
    assert "ADD COLUMN IF NOT EXISTS claim_fingerprint TEXT" in schema
    assert "claim_fingerprint=%s" in (ROOT / "koradaso_publications.py").read_text()
