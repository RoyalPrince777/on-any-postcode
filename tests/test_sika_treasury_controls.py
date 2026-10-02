import pytest

from mission_control import sika_treasury_controls


def test_treasury_snapshot_calculates_free_liquidity():
    state = sika_treasury_controls.snapshot(
        available_sika="12500",
        committed_sika="3250",
        tax_reserved_sika="1900",
        operating_reserve_sika="2000",
    )
    assert state.free_liquidity_sika == 5350
    assert state.shortfall_sika == 0
    assert state.executable is False


def test_treasury_snapshot_reports_shortfall_without_negative_liquidity():
    state = sika_treasury_controls.snapshot(
        available_sika="100",
        committed_sika="80",
        tax_reserved_sika="40",
        operating_reserve_sika="10",
    )
    assert state.free_liquidity_sika == 0
    assert state.shortfall_sika == 30


def test_treasury_release_gate_never_authorises_payment():
    state = sika_treasury_controls.snapshot(available_sika="100")
    gate = sika_treasury_controls.release_gate(state)
    assert gate["liquidity_healthy"] is True
    assert gate["may_enter_payment_review"] is True
    assert gate["payment_execution_authorised"] is False
    assert gate["money_moved"] is False
    assert gate["provider_adapter_required"] is True


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("available_sika", "-1", "available_sika_invalid"),
        ("committed_sika", "NaN", "committed_sika_invalid"),
        ("tax_reserved_sika", "Infinity", "tax_reserved_sika_invalid"),
        ("operating_reserve_sika", "-5", "operating_reserve_sika_invalid"),
    ],
)
def test_invalid_treasury_inputs_fail_closed(field, value, message):
    kwargs = {"available_sika": "100"}
    kwargs[field] = value
    with pytest.raises(sika_treasury_controls.TreasuryError, match=message):
        sika_treasury_controls.snapshot(**kwargs)
