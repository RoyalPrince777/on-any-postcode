"""OAP Open Cinema local byte-integrity regression tests."""
from __future__ import annotations

from hashlib import sha256
from uuid import uuid4

from mission_control import open_cinema_byte_integrity as check


def test_matching_bytes_are_not_legal_rights_or_playback_proof():
    raw = b"non-secret local evidence fixture"
    row = {"evidence_id": str(uuid4()), "sha256": sha256(raw).hexdigest(),
           "rights_verified": True, "worldwide": True}
    result = check.check_bytes(row, raw)
    assert result["digest_match"] is True
    assert result["bytes_checked"] is True
    assert result["country_rights_verified"] is False
    assert result["source_authenticity_verified"] is False
    assert result["licensor_authority_verified"] is False
    assert result["chain_of_title_verified"] is False
    assert result["document_retained"] is False
    assert result["playback_enabled"] is False
    assert result["publication_enabled"] is False
    assert "rights_verified" not in result


def test_modified_bytes_fake_digest_and_missing_evidence_fail_closed():
    raw = b"original"
    digest = sha256(raw).hexdigest()
    row = {"evidence_id": str(uuid4()), "sha256": digest}
    for evidence, document in (
        (row, b"modified"),
        ({**row, "sha256": digest.upper()}, raw),
        ({**row, "sha256": "x" * 64}, raw),
        ({**row, "evidence_id": "invalid"}, raw),
        (row, b""),
        (row, None),
        (row, bytearray(raw)),
        (row, b"x" * (check.MAX_BYTES + 1)),
    ):
        result = check.check_bytes(evidence, document)
        assert result["digest_match"] is False
        assert result["country_rights_verified"] is False
        assert result["playback_enabled"] is False


def test_no_network_filesystem_persistence_or_public_route():
    from pathlib import Path

    source = Path("mission_control/open_cinema_byte_integrity.py").read_text()
    for forbidden in ("requests.", "urlopen(", "open(", "write(", "send_file(",
                      "Blueprint(", "@bp.", "INSERT INTO", "media_ref"):
        assert forbidden not in source
