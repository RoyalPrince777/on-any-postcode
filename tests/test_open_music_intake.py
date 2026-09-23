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
    assert result["canonical_catalogue"] == "OAP Music"
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


def test_asset_integrity_match_is_not_independent_rights_proof():
    import hashlib

    uid = str(uuid4())
    asset = b"locally supplied music bytes"
    digest = hashlib.sha256(asset).hexdigest()
    match = music.asset_integrity_review(uid, asset, digest)
    assert match["digest_matches_submission"] is True
    assert match["independent_source_provenance_verified"] is False
    assert match["rights_verified"] is False
    assert match["playback_enabled"] is False
    assert match["public_catalogue_enabled"] is False
    assert music.asset_integrity_review(uid, b"tampered", digest)["digest_matches_submission"] is False
    assert music.asset_integrity_review("not-uuid", asset, digest)["digest_matches_submission"] is False
    assert music.asset_integrity_review(uid, asset, "A" * 64)["digest_matches_submission"] is False


def test_discovery_directory_never_claims_source_or_import_authority():
    directory = music.source_directory()
    kinds = {entry["source_kind"] for entry in directory["entries"]}
    assert kinds == music.SOURCE_KINDS
    assert directory["canonical_catalogue"] == "OAP Music"
    assert directory["source_fetch_performed"] is False
    assert directory["catalogue_write_performed"] is False
    assert all(entry["connected"] is False for entry in directory["entries"])
    assert all(entry["licence_verified"] is False for entry in directory["entries"])
    assert all(entry["bulk_import_allowed"] is False for entry in directory["entries"])


def test_music_handoff_is_inert_even_with_false_approval_flags():
    candidate = _candidate(rights_verified=True, founder_approved=True,
                           playback_enabled=True, media_url="https://example.test/x")
    result = music.music_handoff_preview(candidate)
    assert result["target_organ"] == "OAP Music"
    assert result["target_release_type"] == "single"
    assert result["handoff_ready"] is False
    assert result["rights_verified"] is False
    assert result["release_created"] is False
    assert result["public_catalogue_enabled"] is False
    assert result["playback_enabled"] is False
    assert "media_url" not in result
    assert music.music_handoff_preview(_candidate(claimed_licence="CC_BY_NC"))["candidate_id"] is None
    assert music.music_handoff_preview(_candidate(candidate_id="broken"))["candidate_id"] is None



def test_nested_untrusted_source_and_licence_fail_closed():
    for bad in ([], {}, {"CC0": True}, ["CC0"]):
        assert music.candidate_preview([_candidate(source_kind=bad)])["candidate_count"] == 0
        assert music.candidate_preview([_candidate(claimed_licence=bad)])["candidate_count"] == 0
        assert music.music_handoff_preview(_candidate(source_kind=bad))["candidate_id"] is None
        assert music.music_handoff_preview(_candidate(claimed_licence=bad))["candidate_id"] is None
        assert music.rights_review({"claimed_licence": bad})["rights_verified"] is False
        assert music.rights_review({"claimed_licence": bad})["claimed_licence"] is None


def test_candidate_preview_never_trusts_caller_approval_or_rights():
    for licence in sorted(music.LICENCE_KINDS):
        item = music.candidate_preview([_candidate(
            claimed_licence=licence, rights_verified=True,
            founder_approved=True, release_created=True
        )])["candidates"][0]
        assert item["rights_verified"] is False
        assert item["music_release_created"] is False
        assert item["playback_enabled"] is False


def test_digest_size_policy_cannot_be_bypassed_or_crash_on_untrusted_types():
    for bad in (None, True, False, 0, -1, 1.0, "8", [], {}, 8_388_609):
        result = music.evidence_bytes_digest(b"evidence", max_bytes=bad)
        assert result["accepted"] is False
        assert result["sha256"] is None
        assert result["rights_verified"] is False
    assert music.evidence_bytes_digest(b"ok", max_bytes=2)["accepted"] is True
    assert music.evidence_bytes_digest(bytearray(b"ok"))["accepted"] is False
    assert music.evidence_bytes_digest(memoryview(b"ok"))["accepted"] is False



def test_rights_review_identifier_is_canonical_and_never_reflects_untrusted_text():
    uid = str(uuid4())
    for identifier in (uid, f"oap:open-music:{uid}"):
        review = music.rights_review({"candidate_id": identifier})
        assert review["candidate_id"] == f"oap:open-music:{uid}"
        assert review["rights_verified"] is False
        assert review["playback_authorised"] is False
    for value in ("<script>alert(1)</script>", "oap:open-music:invalid", ["x"], {}, None):
        review = music.rights_review({"candidate_id": value})
        assert review["candidate_id"] is None
        assert review["rights_verified"] is False
        assert review["distribution_authorised"] is False


def test_preview_candidate_flows_to_private_music_handoff_without_release():
    preview = music.candidate_preview([_candidate()])
    item = preview["candidates"][0]
    handoff = music.music_handoff_preview(item)
    assert handoff["candidate_id"] == item["candidate_id"]
    assert handoff["title"] == item["title"]
    assert handoff["artist"] == item["artist"]
    assert handoff["target_organ"] == "OAP Music"
    assert handoff["handoff_ready"] is False
    assert handoff["release_created"] is False
    assert handoff["playback_enabled"] is False


def test_canonical_candidate_integrity_and_prefix_injection_fail_closed():
    import hashlib

    uid = str(uuid4())
    canonical = f"oap:open-music:{uid}"
    digest = hashlib.sha256(b"asset").hexdigest()
    integrity = music.asset_integrity_review(canonical, b"asset", digest)
    assert integrity["candidate_id"] == canonical
    assert integrity["digest_matches_submission"] is True
    assert integrity["rights_verified"] is False
    assert integrity["playback_enabled"] is False
    for invalid in (
        f"oap:open-music:oap:open-music:{uid}",
        f"oap:another:{uid}",
        f"oap:open-music:{uid}:extra",
        "<script>alert(1)</script>",
        [],
        {},
        None,
    ):
        assert music.music_handoff_preview(_candidate(candidate_id=invalid))["candidate_id"] is None
        assert music.rights_review({"candidate_id": invalid})["candidate_id"] is None
        assert music.asset_integrity_review(invalid, b"asset", digest)["digest_matches_submission"] is False


def test_invalid_or_duplicate_leads_do_not_consume_private_candidate_quota():
    invalid = [_candidate(candidate_id="not-a-uuid") for _ in range(25)]
    valid = _candidate()
    result = music.candidate_preview(invalid + [valid, valid])
    assert result["candidate_count"] == 1
    assert result["candidates"][0]["candidate_id"].endswith(valid["candidate_id"])
    assert result["ingest_performed"] is False


def test_free_music_lead_scan_and_accepted_candidate_quotas_are_bounded():
    rows = [_candidate() for _ in range(music.MAX_LEADS_SCAN + 10)]
    result = music.candidate_preview(rows)
    assert result["candidate_count"] == music.MAX_CANDIDATES
    assert all(c["rights_verified"] is False for c in result["candidates"])
    assert all(c["playback_enabled"] is False for c in result["candidates"])
    hidden = _candidate()
    beyond_scan = [_candidate(candidate_id="bad") for _ in range(music.MAX_LEADS_SCAN)]
    excluded = music.candidate_preview(beyond_scan + [hidden])
    assert excluded["candidate_count"] == 0
    assert excluded["ingest_performed"] is False



def test_allowlisted_open_source_page_is_private_reference_not_rights_proof():
    pages = {
        "free_music_archive": "https://freemusicarchive.org/music/example/",
        "ccmixter": "https://dig.ccmixter.org/files/artist/123",
        "internet_archive": "https://archive.org/details/example-recording",
        "musopen": "https://musopen.org/music/123/example/",
    }
    for source_kind, source_page_url in pages.items():
        item = music.candidate_preview([_candidate(
            source_kind=source_kind, claimed_licence="CC_BY",
            source_page_url=source_page_url, rights_verified=True,
            public_catalogue_enabled=True,
        )])["candidates"][0]
        assert item["source_page_url"] == source_page_url
        assert item["source_page_independently_checked"] is False
        assert item["rights_verified"] is False
        assert item["playback_enabled"] is False
        handoff = music.music_handoff_preview(item)
        assert "source_page_url" not in handoff
        assert handoff["handoff_ready"] is False


def test_open_music_source_page_rejects_spoofed_external_and_tracking_urls():
    hostile = (
        "http://archive.org/details/sample",
        "https://archive.org.evil.test/details/sample",
        "https://archive.org@evil.test/details/sample",
        "https://evil.test@archive.org/details/sample",
        "https://archive.org:443/details/sample",
        "https://archive.org/details/sample?tracking=1",
        "https://archive.org/details/sample#fragment",
        "https://archive.org/",
        "https://archive.org//evil.test/path",
        "https://127.0.0.1/details/sample",
        "https://archive.org/details/sample\nX:injected",
        "https://archive.org/details/sample\\\\evil.test",
        "https://archive.org/details/sample inside",
        ["https://archive.org/details/sample"],
        {"url": "https://archive.org/details/sample"},
    )
    for url in hostile:
        item = music.candidate_preview([_candidate(
            source_kind="internet_archive", source_page_url=url,
        )])["candidates"][0]
        assert item["source_page_url"] is None
        assert item["rights_verified"] is False
        assert item["public_catalogue_enabled"] is False
    for kind in ("direct_artist", "other_open_archive"):
        item = music.candidate_preview([_candidate(
            source_kind=kind,
            source_page_url="https://archive.org/details/unrelated",
        )])["candidates"][0]
        assert item["source_page_url"] is None
    wrong_source = music.candidate_preview([_candidate(
        source_kind="musopen",
        source_page_url="https://archive.org/details/not-musopen",
    )])["candidates"][0]
    assert wrong_source["source_page_url"] is None



def test_private_rights_review_carries_source_reference_without_promoting_claims():
    preview = music.candidate_preview([_candidate(
        source_kind="internet_archive", claimed_licence="CC_BY",
        source_page_url="https://archive.org/details/sample",
    )])["candidates"][0]
    review = music.rights_review(preview, {
        "independently_verified": True, "rights_verified": True,
    })
    assert review["candidate_id"] == preview["candidate_id"]
    assert review["source_kind"] == "internet_archive"
    assert review["source_page_url"] == preview["source_page_url"]
    assert review["source_page_independently_checked"] is False
    assert "verify_recording_rights_separately" in review["review_topics"]
    assert "verify_composition_rights_separately" in review["review_topics"]
    assert "verify_credit_and_licence_notice_requirements" in review["review_topics"]
    assert review["rights_verified"] is False
    assert review["playback_authorised"] is False
    assert review["distribution_authorised"] is False


def test_claimed_music_licences_only_change_review_questions():
    expected = {
        "CC0": "verify_recording_and_composition_public_domain_separately",
        "PUBLIC_DOMAIN": "verify_recording_and_composition_public_domain_separately",
        "CC_BY": "verify_credit_and_licence_notice_requirements",
        "CC_BY_SA": "verify_share_alike_scope_for_planned_uses",
        "DIRECT_PERMISSION": "verify_direct_grant_signatory_scope_and_expiry",
    }
    for licence, topic in expected.items():
        review = music.rights_review(_candidate(
            claimed_licence=licence, rights_verified=True,
        ))
        assert topic in review["review_topics"]
        assert review["rights_verified"] is False
        assert review["source_page_independently_checked"] is False
        assert review["public_catalogue_enabled"] is False
    invalid = music.rights_review(_candidate(
        source_kind="internet_archive", claimed_licence="CC_BY_NC",
        source_page_url="https://evil.test/x", rights_verified=True,
    ))
    assert invalid["claimed_licence"] is None
    assert invalid["source_page_url"] is None
    assert invalid["rights_verified"] is False



def test_real_named_fma_track_can_be_prepared_only_as_private_review_lead():
    # Named source-page fixture, not a downloaded/verified recording or clearance.
    from uuid import UUID

    item = music.candidate_preview([_candidate(
        candidate_id=str(UUID("316822c4-0d81-4944-a413-d33e49c11710")),
        title="Window", artist="1000 Handz",
        source_kind="free_music_archive", claimed_licence="CC_BY",
        source_page_url=(
            "https://freemusicarchive.org/music/1000-handz/"
            "cc-by-free-to-use-melodic-rap-instrumentals/window-1/"
        ),
        rights_verified=True, source_page_independently_checked=True,
    )])["candidates"][0]
    receipt = music.private_source_review_receipt(item)
    assert receipt["title"] == "Window"
    assert receipt["artist"] == "1000 Handz"
    assert receipt["source_page_url"] == item["source_page_url"]
    assert receipt["attribution_draft"] == "Window — 1000 Handz"
    assert receipt["attribution_source_url"] == item["source_page_url"]
    assert receipt["claimed_licence_reference_url"] == (
        "https://creativecommons.org/licenses/by/4.0/"
    )
    assert receipt["attribution_changes_disclosure_review_required"] is True
    assert receipt["review_state"] == "private_unverified_lead"
    assert receipt["receipt_persisted"] is False
    for key in (
        "source_page_independently_checked", "recording_rights_verified",
        "composition_rights_verified", "licensor_authority_verified",
        "territory_and_use_verified", "attribution_verified",
        "source_asset_integrity_verified", "evidence_bytes_retained",
        "music_release_created", "playback_enabled", "public_catalogue_enabled",
    ):
        assert receipt[key] is False


def test_private_source_review_receipt_rejects_hostile_or_unrelated_claims():
    for row in (
        {"candidate_id": "<script>", "title": "Window", "artist": "Claimant"},
        _candidate(candidate_id="broken", source_page_url="https://evil.test/x"),
        [], None,
    ):
        receipt = music.private_source_review_receipt(row)
        assert receipt["candidate_id"] is None
        assert receipt["source_page_url"] is None
        assert receipt["attribution_draft"] is None
        assert receipt["playback_enabled"] is False
        assert receipt["receipt_persisted"] is False
    receipt = music.private_source_review_receipt(_candidate(
        source_kind="free_music_archive",
        source_page_url="https://evil.test/track",
        claimed_licence="CC_BY",
        rights_verified=True,
    ))
    assert receipt["source_page_url"] is None
    assert receipt["recording_rights_verified"] is False
    assert receipt["composition_rights_verified"] is False



def test_licence_reference_is_only_a_reference_not_actual_music_clearance():
    expected = {
        "CC_BY": "https://creativecommons.org/licenses/by/4.0/",
        "CC_BY_SA": "https://creativecommons.org/licenses/by-sa/4.0/",
        "CC0": "https://creativecommons.org/publicdomain/zero/1.0/",
        "PUBLIC_DOMAIN": None,
        "DIRECT_PERMISSION": None,
    }
    for claim, link in expected.items():
        result = music.private_source_review_receipt(_candidate(
            claimed_licence=claim, rights_verified=True,
            recording_rights_verified=True, composition_rights_verified=True,
        ))
        assert result["claimed_licence_reference_url"] == link
        assert result["attribution_verified"] is False
        assert result["recording_rights_verified"] is False
        assert result["composition_rights_verified"] is False
        assert result["playback_enabled"] is False



def test_private_release_plan_is_one_owner_aware_review_not_release_authority():
    from uuid import uuid4

    owner = str(uuid4())
    release_id = str(uuid4())
    lead = music.candidate_preview([_candidate(
        source_kind="free_music_archive", claimed_licence="CC_BY",
        source_page_url="https://freemusicarchive.org/music/sample/track/",
        rights_verified=True, founder_approved=True,
    )])["candidates"][0]
    plan = music.private_music_release_review_plan(lead, owner, release_id)
    assert plan["candidate_id"] == lead["candidate_id"]
    assert plan["submitted_owner_identity_id"] == owner
    assert plan["submitted_release_id"] == release_id
    assert plan["owner_authenticated"] is False
    assert plan["owner_bound_to_music_release"] is False
    assert plan["target_organ"] == "OAP Music"
    assert plan["target_release_type"] == "single"
    assert plan["source_page_url"] == lead["source_page_url"]
    assert plan["attribution_draft"] == lead["title"] + " — " + lead["artist"]
    assert len(plan["review_requirements"]) == 8
    assert all(not row["independently_proven"] for row in plan["review_requirements"])
    assert plan["private_plan_only"] is True
    for field in (
        "ready_for_authenticated_handoff", "independent_rights_verified",
        "asset_provenance_verified", "human_release_approved",
        "receipt_persisted", "release_created", "media_retrieval_performed",
        "public_catalogue_enabled", "playback_enabled", "payments_enabled",
    ):
        assert plan[field] is False


def test_private_release_plan_rejects_unauthenticated_or_malformed_claims():
    from uuid import uuid4

    good = _candidate(rights_verified=True, owner_authenticated=True,
                      public_catalogue_enabled=True, human_release_approved=True)
    for owner in (str(uuid4()), "not-uuid", [], {"owner": str(uuid4())}, None):
        plan = music.private_music_release_review_plan(good, owner)
        assert plan["owner_authenticated"] is False
        assert plan["human_release_approved"] is False
        assert plan["ready_for_authenticated_handoff"] is False
        assert plan["playback_enabled"] is False
        if not isinstance(owner, str) or owner == "not-uuid":
            assert plan["submitted_owner_identity_id"] is None
    for bad in ({}, None, [], {"candidate_id": "spoofed", "title": "x"}):
        plan = music.private_music_release_review_plan(bad, str(uuid4()))
        assert plan["candidate_id"] is None
        assert plan["submitted_owner_identity_id"] is None
        assert plan["target_release_type"] is None
        assert plan["release_created"] is False



def test_release_uuid_is_untrusted_and_never_unlocks_existing_release():
    from uuid import uuid4

    owner, release = str(uuid4()), str(uuid4())
    for submitted in (release, "not-a-uuid", None, [release], {"id": release}):
        plan = music.private_music_release_review_plan(
            _candidate(owner_authenticated=True, owner_bound_to_music_release=True,
                       human_release_approved=True), owner, submitted
        )
        assert plan["submitted_release_id"] == (
            release if submitted == release else None
        )
        assert plan["owner_authenticated"] is False
        assert plan["owner_bound_to_music_release"] is False
        assert plan["ready_for_authenticated_handoff"] is False
        assert plan["release_created"] is False
        assert plan["public_catalogue_enabled"] is False
        assert plan["playback_enabled"] is False
    invalid = music.private_music_release_review_plan(
        {"candidate_id": "bad", "title": "fake"}, owner, release
    )
    assert invalid["submitted_release_id"] is None
    assert invalid["submitted_owner_identity_id"] is None
