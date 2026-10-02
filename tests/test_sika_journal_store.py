import pytest

from mission_control import sika_double_entry, sika_journal_store


def _batch():
    return sika_double_entry.validate_batch(
        journal_id="journal-1",
        reference="proof-1",
        lines=[
            sika_double_entry.line(
                account_id="cash",
                side="debit",
                amount="100.00",
                currency="GBP",
            ),
            sika_double_entry.line(
                account_id="customer-liability",
                side="credit",
                amount="100.00",
                currency="GBP",
            ),
        ],
    )


def test_reversal_batch_is_equal_and_opposite():
    original = _batch()
    reversal = sika_double_entry.reversal_batch(
        original=original,
        journal_id="journal-2",
        reference="reverse-proof-1",
    )
    assert reversal.balanced is True
    assert reversal.lines[0].side is sika_double_entry.Side.CREDIT
    assert reversal.lines[1].side is sika_double_entry.Side.DEBIT
    assert reversal.lines[0].amount == original.lines[0].amount
    assert reversal.lines[1].amount == original.lines[1].amount


def test_journal_store_schema_enforces_database_immutability():
    sql = "\n".join(sika_journal_store.SCHEMA_STATEMENTS)
    assert "BEFORE UPDATE OR DELETE ON oap_sika_journals" in sql
    assert "BEFORE UPDATE OR DELETE ON oap_sika_journal_lines" in sql
    assert "sika_journal_is_immutable" in sql


def test_journal_store_requires_explicit_human_schema_approval():
    with pytest.raises(RuntimeError, match="Explicit human approval required"):
        sika_journal_store.init_schema()


def test_journal_store_dry_run_moves_no_money():
    state = sika_journal_store.init_schema(assume_yes=True, dry_run=True)
    assert state["schema_ready"] is False
    assert state["human_authority_final"] is True


def test_journal_store_status_is_append_only_and_non_settling():
    status = sika_journal_store.status()
    assert status["append_only"] is True
    assert status["database_mutation_protection"] is True
    assert status["supports_compensating_reversals"] is True
    assert status["in_place_update_allowed"] is False
    assert status["in_place_delete_allowed"] is False
    assert status["settlement_execution"] is False
    assert status["external_money_movement"] is False
