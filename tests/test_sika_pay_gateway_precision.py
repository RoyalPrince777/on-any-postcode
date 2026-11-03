"""SIKA Pay gateway rejects amounts that would silently change at cent precision."""
import pytest

from mission_control import sika_pay_gateway


@pytest.mark.parametrize("value", ["0.001", "0.009", "1.001", "1.005", "1.999", "0", "-1", "NaN", "Infinity"])
def test_invalid_cent_precision_is_rejected(value):
    with pytest.raises(sika_pay_gateway.SikaPayGatewayError, match="amount_invalid"):
        sika_pay_gateway._amount(value)


@pytest.mark.parametrize("value, expected", [("0.01", "0.01"), ("1.20", "1.20"), ("1.000", "1.00")])
def test_exact_cents_preserved(value, expected):
    assert sika_pay_gateway._amount(value) == expected
