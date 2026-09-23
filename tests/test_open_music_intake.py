"""Negative tests for bounded private OAP Open Music intake."""
from uuid import uuid4

from mission_control import open_music_intake as music


def _candidate(**changes):
    row = {
        "candidate_id": str(uuid4()),
        "title": "Independent recording",
        "artist": "Artist",
        "source_kind": "direct_artist",
        "claimed_licence": "DIRECT_PERMISSION",
    }
    row.update(changes)
    return row


def test_private_candidate_never_claims_ingest_or_playback():
    result = music.candidate_preview([_candidate()])
    assert result["candidate_count"] == 1
    assert result["canonical_catalogue"] == "OAP Tune Core"
    assert result["ingest_performed"] is False
    assert result["candidates"][0]["rights_verified"] is False
    assert result["candidates"][0]["playback_enabled"] is False


def test_reject_invalid_leads_and_duplicate_ids():
    row = _candidate()
    result = music.candidate_preview([
        row, row, _candidate(claimed_licence="CC_BY_NC"),
        _candidate(source_kind="Spotify"),
        _candidate(title=" "),
        {"candidate_id": "not-a-uuid"},
    ])
    assert result["candidate_count"] == 1


def test_untrusted_candidate_cannot_inject_media_url_or_approval():
    result = music.candidate_preview([_candidate(
        media_url="https://example.test/audio.mp3",
        rights_verified=True,
        playback_enabled=True,
        public_catalogue_enabled=True,
    )])
    item = result["candidates"][0]
    assert "media_url" not in item
    assert item["rights_verified"] is False
    assert item["public_catalogue_enabled"] is False


def test_digest_is_actual_bytes_not_asserted_source_integrity():
    digest = music.evidence_bytes_digest(b"evidence")
    assert digest["accepted"] is True
    assert len(digest["sha256"]) == 64
    assert digest["independently_verified"] is False
    assert digest["rights_verified"] is False
    assert music.evidence_bytes_digest("claimed hash")["accepted"] is False
    assert music.evidence_bytes_digest(b"")["accepted"] is False
    assert music.evidence_bytes_digest(b"xx", max_bytes=1)["accepted"] is False


def test_rights_review_rejects_applicant_supplied_proofs():
    result = music.rights_review(
        {"candidate_id": "claimed", "claimed_licence": "CC0", "rights_verified": True},
        {"evidence_id": str(uuid4()), "independently_verified": True},
    )
    assert result["submitted_evidence_id"] is not None
    assert result["rights_verified"] is False
    assert result["source_bytes_verified"] is False
    assert result["playback_authorised"] is False
    assert result["distribution_authorised"] is False
    assert result["human_authority_final"] is True
