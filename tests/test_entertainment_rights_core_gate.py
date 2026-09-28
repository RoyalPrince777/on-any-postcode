from mission_control import entertainment_catalogue


def _record():
    return {
        "content_id": "oap:tune:7fa79d7e-3ed1-4efc-a1b6-f751ebd5ca20",
        "publication_state": "PUBLISHED",
        "rights_review_state": "VERIFIED",
    }


def _decision(**overrides):
    row = {
        "decision": "ALLOW",
        "decision_hash": "a" * 64,
        "evidence_hashes": ["b" * 64],
        "authority_receipt_hashes": ["c" * 64],
        "human_approval_receipt_hashes": ["d" * 64],
        "public_distribution_authorized": False,
    }
    row.update(overrides)
    return row


def test_player_rights_gate_accepts_only_structured_canonical_allow():
    result = entertainment_catalogue.rights_gate(
        _record(),
        _decision(),
        media_integrity_proven=True,
        entitlement_proven=True,
    )
    assert result["allowed"] is True
    assert result["independent_proof_checked"] is True
    assert result["playback_authorised"] is True
    assert result["media_delivery_performed"] is False


def test_rights_allow_does_not_enable_media_delivery_or_stream_url():
    player = entertainment_catalogue.universal_player_contract(
        _record(),
        _decision(),
        media_integrity_proven=True,
        entitlement_proven=True,
    )
    assert player["rights_eligible"] is True
    assert player["playback_enabled"] is False
    assert player["stream_url"] is None
    assert player["media_delivery_performed"] is False
    assert player["external_distribution_performed"] is False


def test_missing_receipts_integrity_or_entitlement_fail_closed():
    cases = [
        (_decision(decision="REVIEW"), True, True),
        (_decision(evidence_hashes=[]), True, True),
        (_decision(authority_receipt_hashes=[]), True, True),
        (_decision(human_approval_receipt_hashes=[]), True, True),
        (_decision(), False, True),
        (_decision(), True, False),
        (None, True, True),
    ]
    for decision, integrity, entitlement in cases:
        result = entertainment_catalogue.rights_gate(
            _record(),
            decision,
            media_integrity_proven=integrity,
            entitlement_proven=entitlement,
        )
        assert result["allowed"] is False
        assert result["playback_authorised"] is False
