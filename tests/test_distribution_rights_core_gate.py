from mission_control import distribution_intelligence


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


def _payload(**overrides):
    row = {
        "title": "OAP release",
        "campaign_ready": True,
        "receipt_destination": True,
        "external_adapter_proven": False,
    }
    row.update(overrides)
    return row


def test_canonical_rights_decision_unlocks_internal_distribution_readiness_only():
    result = distribution_intelligence.review_release_with_rights_decision(
        _payload(), _decision()
    )
    assert result["rights_core_checked"] is True
    assert result["legacy_rights_boolean_used"] is False
    assert result["owned_oap_distribution_ready"] is True
    assert result["external_distribution_ready"] is False
    assert result["execution_performed"] is False
    assert result["publishing_authority_granted"] is False


def test_rights_review_or_missing_receipts_fail_closed():
    cases = [
        _decision(decision="REVIEW"),
        _decision(evidence_hashes=[]),
        _decision(authority_receipt_hashes=[]),
        _decision(human_approval_receipt_hashes=[]),
        _decision(public_distribution_authorized=True),
        {},
        None,
    ]
    for decision in cases:
        result = distribution_intelligence.review_release_with_rights_decision(
            _payload(), decision
        )
        assert result["owned_oap_distribution_ready"] is False
        assert result["external_distribution_ready"] is False
        assert result["execution_performed"] is False


def test_external_route_never_self_executes_even_when_all_internal_gates_pass():
    result = distribution_intelligence.review_release_with_rights_decision(
        _payload(external_adapter_proven=True), _decision()
    )
    assert result["external_distribution_ready"] is True
    assert result["execution_performed"] is False
    assert result["publishing_authority_granted"] is False
    assert result["payment_authority_granted"] is False
    assert result["human_authority_final"] is True
