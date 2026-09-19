"""Contract checks for a display-only SIKA Manifest quote."""
import pytest

from mission_control.sika_quote import quote_manifest


def test_no_manifest_has_no_allocation():
    quote = quote_manifest(100)
    assert (quote.total_pence, quote.area_allocation_pence) == (100, 0)
    assert quote.status == "QUOTE_ONLY_NO_PAYMENT"


def test_seven_percent_only_on_optional_manifest():
    quote = quote_manifest(100, 200, "postcode")
    assert (quote.total_pence, quote.area_allocation_pence, quote.remaining_manifest_pence) == (300, 14, 186)


def test_rounds_to_whole_pence_without_float():
    assert quote_manifest(100, 7, "borough").area_allocation_pence == 0
    assert quote_manifest(100, 8, "borough").area_allocation_pence == 1


@pytest.mark.parametrize("bad", [-1, 1.0, True, "100", None])
def test_rejects_invalid_money(bad):
    with pytest.raises(ValueError):
        quote_manifest(bad)


def test_requires_area_choice_when_manifest_selected():
    with pytest.raises(ValueError):
        quote_manifest(100, 100)


def test_rejects_arbitrary_area_and_overflow():
    with pytest.raises(ValueError):
        quote_manifest(100, 100, "unknown")
    with pytest.raises(ValueError):
        quote_manifest(10_000_000_00, 1, "postcode")
