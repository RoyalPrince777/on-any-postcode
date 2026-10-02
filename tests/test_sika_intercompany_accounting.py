import pytest

from mission_control import sika_intercompany_accounting


def _pair(*, left_due_from="100", right_due_to="100"):
    left = sika_intercompany_accounting.position(
        entity_id="Europa Crown Bank UK",
        counterparty_entity_id="Africa Crown Bank Ghana",
        jurisdiction="United Kingdom",
        counterparty_jurisdiction="Ghana",
        currency="GBP",
        due_from=left_due_from,
        due_to="0",
        reference="ic-777",
    )
    right = sika_intercompany_accounting.position(
        entity_id="Africa Crown Bank Ghana",
        counterparty_entity_id="Europa Crown Bank UK",
        jurisdiction="Ghana",
        counterparty_jurisdiction="United Kingdom",
        currency="GBP",
        due_from="0",
        due_to=right_due_to,
        reference="ic-777",
    )
    return left, right


def test_matching_intercompany_balances_are_elimination_ready():
    left, right = _pair()
    result = sika_intercompany_accounting.match(left=left, right=right)
    assert result.state == "MATCHED"
    assert result.matched_amount == 100
    assert result.difference == 0
    assert result.elimination_ready is True
    assert result.cross_jurisdiction is True
    assert result.money_pooled is False
    assert result.settlement_executed is False


def test_mismatch_requires_resolution_before_elimination():
    left, right = _pair(left_due_from="100", right_due_to="95")
    result = sika_intercompany_accounting.match(left=left, right=right)
    assert result.state == "MISMATCH"
    assert result.difference == 5
    assert result.elimination_ready is False


def test_entity_pair_mismatch_fails_closed():
    left, _right = _pair()
    bad = sika_intercompany_accounting.position(
        entity_id="Pacific Crown Bank",
        counterparty_entity_id="Europa Crown Bank UK",
        jurisdiction="Pacific",
        counterparty_jurisdiction="United Kingdom",
        currency="GBP",
        due_to="100",
        reference="ic-777",
    )
    with pytest.raises(
        sika_intercompany_accounting.IntercompanyAccountingError,
        match="entity_pair_mismatch",
    ):
        sika_intercompany_accounting.match(left=left, right=bad)


def test_same_entity_position_is_rejected():
    with pytest.raises(
        sika_intercompany_accounting.IntercompanyAccountingError,
        match="entities_must_differ",
    ):
        sika_intercompany_accounting.position(
            entity_id="Europa Crown Bank UK",
            counterparty_entity_id="Europa Crown Bank UK",
            jurisdiction="United Kingdom",
            counterparty_jurisdiction="United Kingdom",
            currency="GBP",
            due_from="1",
            reference="bad",
        )


def test_status_keeps_entities_and_money_separate():
    status = sika_intercompany_accounting.status()
    assert status["first_party"] is True
    assert status["legal_entities_collapsed"] is False
    assert status["cross_jurisdiction_money_pooling"] is False
    assert status["settlement_execution"] is False
    assert status["money_movement"] is False
