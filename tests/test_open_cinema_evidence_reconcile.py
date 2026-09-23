"""Film evidence reconciliation never confuses byte-match with licence."""
from __future__ import annotations

from hashlib import sha256
from uuid import uuid4

from mission_control import open_cinema_evidence_reconcile as contract


def _inputs():
    document = b"isolated film evidence fixture"
    evidence = {
        "evidence_id": str(uuid4()),
        "kind": "signed_distribution_agreement",
        "sha256": sha256(document).hexdigest(),
        "rights_approved": True,
    }
    territory = {
        "country": "GB", "models": ["FREE_TO_VIEW"],
        "starts_on": "2026-01-01", "ends_on": "2026-12-31",
        "worldwide": True,
    }
    uid = str(uuid4())
    evidence.update({
        "candidate_id": f"oap:open-cinema:{uid}",
        "country": territory["country"],
        "models": list(territory["models"]),
        "starts_on": territory["starts_on"],
        "ends_on": territory["ends_on"],
    })
    return uid, territory, evidence, document


def test_matching_local_evidence_receipt_never_authorises_rights():
    uid, territory, evidence, document = _inputs()
    result = contract.reconcile(
        uid, territory, evidence, document, today="2026-09-23"
    )
    assert result["private_review_receipt_complete"] is True
    assert result["local_digest_matches_submission"] is True
    assert result["claim_binding_matches_submission"] is True
    assert result["country"] == "GB"
    assert result["independent_source_attested"] is False
    assert result["licensor_authority_verified"] is False
    assert result["country_rights_verified"] is False
    assert result["licence_acquired"] is False
    assert result["publication_enabled"] is False
    assert result["playback_enabled"] is False
    assert result["recovery"] == "await_independent_rights_authority"


def test_mutated_bytes_and_expired_or_future_window_invalidate_receipt():
    uid, territory, evidence, document = _inputs()
    for row, payload, today in (
        (territory, b"changed", "2026-09-23"),
        (territory, document, "2027-01-01"),
        (territory, document, "2025-12-31"),
        (territory, document, "bad-date"),
        ({**territory, "country": "WORLD"}, document, "2026-09-23"),
        ({**territory, "models": ["UNKNOWN"]}, document, "2026-09-23"),
    ):
        result = contract.reconcile(uid, row, evidence, payload, today=today)
        assert result["private_review_receipt_complete"] is False
        assert result["country_rights_verified"] is False
        assert result["playback_enabled"] is False
        assert result["recovery"] == "resubmit_evidence_and_repeat_independent_review"


def test_invalid_reference_and_forged_flags_cannot_bypass():
    uid, territory, evidence, document = _inputs()
    result = contract.reconcile(
        uid, territory, {**evidence, "evidence_id": "not-a-uuid",
                         "digest_match": True, "founder_approved": True},
        document, today="2026-09-23",
    )
    assert result["private_review_receipt_complete"] is False
    assert result["licence_acquired"] is False
    assert result["playback_enabled"] is False


def test_cross_film_and_cross_territory_replay_denied_even_with_matching_bytes():
    uid, territory, evidence, document = _inputs()
    for candidate, claim, submitted in (
        (str(uuid4()), territory, evidence),
        (uid, {**territory, "country": "GH"}, evidence),
        (uid, {**territory, "models": ["AVOD"]}, evidence),
        (uid, {**territory, "ends_on": "2027-12-31"}, evidence),
        (uid, territory, {**evidence, "candidate_id": str(uuid4())}),
        (uid, territory, {**evidence, "models": ["SVOD"]}),
    ):
        result = contract.reconcile(
            candidate, claim, submitted, document, today="2026-09-23"
        )
        assert result["local_digest_matches_submission"] is True
        assert result["claim_binding_matches_submission"] is False
        assert result["private_review_receipt_complete"] is False
        assert "evidence_not_bound_to_exact_candidate_country_models_window" in (
            result["blockers"]
        )
        assert result["country_rights_verified"] is False
        assert result["playback_enabled"] is False


def test_missing_binding_and_forged_signoff_cannot_complete_receipt():
    uid, territory, evidence, document = _inputs()
    for changed in (
        {key: value for key, value in evidence.items() if key != "country"},
        {**evidence, "models": "FREE_TO_VIEW"},
        {**evidence, "models": ["FREE_TO_VIEW", "FREE_TO_VIEW"]},
        {**evidence, "source_attested": True, "chain_of_title_verified": True},
    ):
        result = contract.reconcile(
            uid, territory, changed, document, today="2026-09-23"
        )
        assert result["country_rights_verified"] is False
        assert result["playback_enabled"] is False
        if changed.get("country") is None or not isinstance(
            changed.get("models"), list
        ) or len(changed["models"]) != 1:
            assert result["private_review_receipt_complete"] is False


def test_no_disk_network_or_media_delivery_in_reconciler():
    from pathlib import Path

    source = Path("mission_control/open_cinema_evidence_reconcile.py").read_text()
    for forbidden in (
        "requests.", "urlopen(", "send_file(", "Blueprint(",
        "INSERT INTO", "media_ref", "open(", "write(",
    ):
        assert forbidden not in source
