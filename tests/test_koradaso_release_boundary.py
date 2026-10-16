"""Pressure tests for Koradaso explicit heritage release consent."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = (ROOT / "mission_control" / "koradaso_schema.py").read_text()
RELEASES = (ROOT / "mission_control" / "koradaso_releases.py").read_text()
PUBLICATIONS = (ROOT / "mission_control" / "koradaso_publications.py").read_text()


def test_release_permission_is_separate_and_not_auto_granted():
    assert "KORADASO_RELEASE_HERITAGE" in SCHEMA
    assert "koradaso_release_consents" in SCHEMA
    assert "oap_role_permissions" not in SCHEMA


def test_release_does_not_grant_royal_status():
    assert '"royal_status_granted": False' in RELEASES
    assert "human_review_required_before_release" in RELEASES


def test_publication_requires_live_release_consent():
    assert "active_release_consent_required" in PUBLICATIONS
    assert "revoked_at IS NULL" in PUBLICATIONS
    release_check = PUBLICATIONS.index("active_release_consent_required")
    publication_insert = PUBLICATIONS.index("INSERT INTO koradaso_publications")
    assert release_check < publication_insert


def test_release_revocation_preserves_ledger():
    assert "DELETE FROM koradaso_release_consents" not in RELEASES
    assert "SET revoked_at=CURRENT_TIMESTAMP" in RELEASES
    assert "KORADASO_HERITAGE_RELEASE_REVOKED" in RELEASES
