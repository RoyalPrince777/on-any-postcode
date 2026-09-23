"""Private Open Cinema evidence envelope tests: no user-minted rights."""
from __future__ import annotations

from uuid import uuid4

from mission_control import open_cinema_evidence as gate


def _territory(**overrides):
    return {
        **{"country": "GB", "models": ["FREE_TO_VIEW"],
           "starts_on": "2026-09-23", "ends_on": "2027-09-23"},
        **overrides,
    }


def _evidence(**overrides):
    return {
        **{"evidence_id": str(uuid4()),
           "kind": "signed_distribution_agreement", "sha256": "a" * 64},
        **overrides,
    }


def test_claimed_evidence_never_verifies_country_rights_or_playback():
    uid = str(uuid4())
    result = gate.review_envelope(
        uid, {**_territory(), "verified": True},
        [{**_evidence(), "rights_granted": True, "integrity_verified": True}],
    )
    assert result["candidate_id"] == f"oap:open-cinema:{uid}"
    assert result["country"] == "GB"
    assert result["evidence_count"] == 1
    assert result["submitted_digests_verified"] is False
    assert result["country_rights_verified"] is False
    assert result["licence_acquired"] is False
    assert result["playback_enabled"] is False
    assert result["review_state"] == "awaiting_independent_review"
    assert "rights_granted" not in result["submitted_evidence"][0]


def test_missing_or_invalid_title_country_window_or_documents_stays_blocked():
    for uid, territory, evidence in (
        ("invalid", _territory(), [_evidence()]),
        (str(uuid4()), _territory(country="WORLD"), [_evidence()]),
        (str(uuid4()), _territory(ends_on="2020-01-01"), [_evidence()]),
        (str(uuid4()), _territory(), [{"evidence_id": str(uuid4()),
                                        "kind": "signed_distribution_agreement",
                                        "sha256": "not-a-real-digest"}]),
        (str(uuid4()), _territory(), []),
    ):
        result = gate.review_envelope(uid, territory, evidence)
        assert result["country_rights_verified"] is False
        assert result["playback_enabled"] is False
        assert result["blockers"]


def test_evidence_dedup_and_bound():
    row = _evidence()
    result = gate.review_envelope(str(uuid4()), _territory(), [row] * 30)
    assert result["evidence_count"] == 1
    assert result["submitted_evidence"][0]["submitted_sha256"] == "a" * 64


def test_founder_review_route_rejects_anonymous_access(anonymous_client):
    url = "/mission/organs/entertainment/open-cinema/evidence-preview"
    assert anonymous_client.post(url, json={
        "candidate_id": str(uuid4()), "territory": _territory(),
        "evidence": [_evidence()],
    }).status_code in (401, 403)
    assert anonymous_client.get(url).status_code in (404, 405)
