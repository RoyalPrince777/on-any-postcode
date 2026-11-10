import pytest

from mission_control import sika_provider_adapter


def _evidence(**overrides):
    values = {
        "provider_id": "example-provider",
        "authority_reference": "authority-evidence-ref",
        "legal_entity_reference": "legal-entity-ref",
        "environment": "sandbox",
        "settlement_receipt_contract": "provider-settlement-receipt-v1",
        "refund_contract": "provider-refund-v1",
    }
    values.update(overrides)
    return sika_provider_adapter.build_evidence(**values)


def test_provider_adapter_reuses_canonical_payment_slot_and_stays_closed():
    state = sika_provider_adapter.status()
    assert state["canonical_provider_fabric_reused"] is True
    assert state["payment_slot_present"] is True
    assert state["payment_execution_enabled"] is False
    assert state["money_movement_enabled"] is False


def test_complete_provider_evidence_only_enters_human_execution_review():
    result = sika_provider_adapter.release_review(_evidence())
    assert result["provider_evidence_complete"] is True
    assert result["may_enter_execution_review"] is True
    assert result["human_authority_required"] is True
    assert result["payment_execution_authorised"] is False
    assert result["money_moved"] is False
    assert result["customer_funds_held"] is False


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("provider_id", "provider_id_required"),
        ("authority_reference", "provider_authority_reference_required"),
        ("legal_entity_reference", "legal_entity_reference_required"),
        ("settlement_receipt_contract", "settlement_receipt_contract_required"),
        ("refund_contract", "refund_contract_required"),
    ],
)
def test_required_provider_evidence_fails_closed(field, message):
    with pytest.raises(sika_provider_adapter.ProviderEvidenceError, match=message):
        _evidence(**{field: ""})


def test_provider_environment_must_be_explicit():
    with pytest.raises(
        sika_provider_adapter.ProviderEvidenceError,
        match="provider_environment_invalid",
    ):
        _evidence(environment="live-ish")


def test_provider_evidence_hash_is_deterministic_and_changes_with_scope():
    first = _evidence()
    second = _evidence()
    changed = _evidence(authority_reference="different-authority")
    assert first.evidence_hash == second.evidence_hash
    assert first.evidence_hash != changed.evidence_hash
