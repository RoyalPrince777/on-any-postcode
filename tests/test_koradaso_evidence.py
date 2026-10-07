"""Pressure tests for Koradaso evidence privacy and lineage."""
from pathlib import Path

SOURCE = Path("mission_control/koradaso_evidence.py").read_text()
SCHEMA = Path("mission_control/koradaso_schema.py").read_text()


def test_private_reads_fail_closed():
    assert 'if scope == "PUBLIC":' in SOURCE
    assert 'if scope == "ME":' in SOURCE
    assert 'return str(identity) == str(created_by)' in SOURCE
    assert 'permission = READ_PERMISSIONS.get(scope)' in SOURCE
    assert 'if permission is None:' in SOURCE
    assert 'return False' in SOURCE
    assert 'raise KoradasoEvidenceDenied("evidence_read_denied")' in SOURCE


def test_scoped_read_permissions_are_explicit_not_auto_granted():
    for permission in (
        "KORADASO_READ_ROYAL_EVIDENCE",
        "KORADASO_READ_FAMILY_EVIDENCE",
        "KORADASO_READ_COMMUNITY_EVIDENCE",
    ):
        assert permission in SOURCE
        assert permission in SCHEMA
    assert "INSERT INTO oap_role_permissions" not in SCHEMA


def test_version_allocation_locks_parent_first():
    lock = 'SELECT evidence_id FROM koradaso_evidence WHERE evidence_id=%s FOR UPDATE'
    latest = 'SELECT COALESCE(MAX(version_number),0) FROM koradaso_evidence_versions'
    assert lock in SOURCE
    assert latest in SOURCE
    assert SOURCE.index(lock) < SOURCE.index(latest)


def test_original_and_later_versions_are_distinct():
    assert "'ORIGINAL'" in SOURCE
    for kind in ("TRANSCRIPTION", "TRANSLATION", "INTERPRETATION", "CORRECTION"):
        assert kind in SOURCE
    assert "original_hash" in SOURCE
    assert "content_hash" in SOURCE


def test_read_projection_does_not_return_source_uri_or_created_by():
    return_block = SOURCE.split("def read_evidence", 1)[1]
    assert '"source_uri":' not in return_block
    assert '"created_by":' not in return_block
