from datetime import UTC, datetime, timedelta
from decimal import Decimal

from mission_control import bank_permission_scope


def _scope(**overrides):
    values = {
        "scope_id": "scope-1",
        "status": "ACCEPTED",
        "authorisation_letter_reference": "letter-ref",
        "part4a_permission_reference": "part4a-ref",
        "financial_services_register_reference": "fsr-ref",
        "effective_from": datetime.now(UTC).date(),
        "mobilisation": False,
        "deposit_cap_gbp": None,
        "permitted_capabilities": frozenset({"accept_deposits", "execute_payments"}),
        "restrictions": (),
    }
    values.update(overrides)
    return bank_permission_scope.PermissionScope(**values)


def test_permission_scope_allows_only_named_effective_capabilities():
    scope = _scope()
    assert scope.allows("accept_deposits") is True
    assert scope.allows("issue_payment_cards") is False


def test_future_permission_scope_is_not_effective():
    scope = _scope(effective_from=datetime.now(UTC).date() + timedelta(days=1))
    assert scope.allows("accept_deposits") is False


def test_mobilisation_scope_preserves_deposit_cap():
    scope = _scope(mobilisation=True, deposit_cap_gbp=Decimal("50000.00"))
    assert scope.mobilisation is True
    assert scope.deposit_cap_gbp == Decimal("50000.00")


def test_unknown_capability_is_never_allowed():
    scope = _scope()
    assert scope.allows("invented_permission") is False
