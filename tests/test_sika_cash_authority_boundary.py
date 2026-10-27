"""Trusted cash authority boundary remains non-executing and fail closed."""
import pytest

from mission_control import sika_cash_authority_boundary as boundary
from mission_control import sika_cash_service_point as cash


def _review(resolver):
    return boundary.assess_with_trusted_records(
        intent_id="cash-001", service_point_id="point-001",
        operator_id="staff-001", customer_reference="customer-001",
        amount="10.00", currency="GBP", direction="CASH_IN",
        resolve_authority=resolver,
    )


def _records(site, operator):
    return {
        "service_point_id": site, "operator_id": operator,
        "staff_authorised": True, "site_verified": True,
        "regulated_cash_authority_proven": True,
    }


def test_trusted_records_validate_without_cashing_out():
    result = _review(_records)
    assert result["intent_validated"] is True
    assert result["cash_execution_enabled"] is False
    assert result["funds_moved"] is False


def test_missing_records_fail_closed():
    with pytest.raises(boundary.CashAuthorityUnavailable):
        _review(lambda site, operator: None)
    with pytest.raises(boundary.CashAuthorityUnavailable):
        _review(lambda site, operator: (_ for _ in ()).throw(OSError("offline")))


def test_site_operator_substitution_is_rejected():
    with pytest.raises(cash.CashServicePointError, match="cash_authority_identity_mismatch"):
        _review(lambda site, operator: _records("another-site", operator))


@pytest.mark.parametrize("field,error", [
    ("staff_authorised", "cash_staff_authority_missing"),
    ("site_verified", "cash_site_unverified"),
    ("regulated_cash_authority_proven", "cash_regulatory_authority_missing"),
])
def test_missing_independent_approval_is_denied(field, error):
    def resolver(site, operator):
        evidence = _records(site, operator)
        evidence[field] = False
        return evidence
    with pytest.raises(cash.CashServicePointError, match=error):
        _review(resolver)
