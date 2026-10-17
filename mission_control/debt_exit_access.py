"""Unregistered, no-write Debt Exit access adapter over existing OAP controls.

Returns a proposed change ONLY. Performs no SQL, HRM writes, HTTP registration,
creditor contact, payment, migration or deployment. A later separately reviewed
service must atomically persist case version and minimal audit receipt.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from oap.identity import IdentityEngine
from oap.permissions import PermissionEngine

from . import web_security
from .debt_exit_truth import (
    _SAFE_REF, Action, ChangeReceipt, DebtCase, TransitionDenied, transition,
)

DEBT_EXIT_REVIEW_PERMISSION = "DEBT_EXIT_REVIEW"


@dataclass(frozen=True, slots=True)
class PendingDebtChange:
    """Not proof of a persisted, audited or financially executed action."""

    case: DebtCase
    receipt: ChangeReceipt
    persisted: bool = False
    hrm_recorded: bool = False
    financially_executed: bool = False


def propose_debt_change(
    case_id: str,
    action: Action,
    *,
    identity_engine: IdentityEngine,
    permission_engine: PermissionEngine,
    load_trusted_case: Callable[[str], DebtCase],
    guardian_review: Callable[[str, str, Action], bool],
    expected_version: int,
    evidence_ref: str | None = None,
) -> PendingDebtChange:
    """Deny before case access unless canonical identity and permission agree.

    Loader and Guardian callback must be internal trusted OAP interfaces, not
    client-supplied booleans. This function intentionally does not register a
    route or constitute functioning production Guardian/Data/HRM integration.
    """
    try:
        user = web_security.current_authenticated_user()
        if user is None or user.get("recovery_founder") is True:
            raise TransitionDenied("access_denied")
        principal = web_security.authenticated_identity()
        identity = identity_engine.validate(principal)
        permitted = permission_engine.authorize_identity(
            identity, required_permission=DEBT_EXIT_REVIEW_PERMISSION
        )
        if not permitted.allowed or identity.identity_id != principal:
            raise TransitionDenied("access_denied")
    except TransitionDenied:
        raise
    except Exception as exc:
        raise TransitionDenied("access_denied") from exc

    if (
        not isinstance(case_id, str)
        or not _SAFE_REF.fullmatch(case_id)
        or not isinstance(action, Action)
    ):
        raise TransitionDenied("invalid_request")
    try:
        if guardian_review(principal, case_id, action) is not True:
            raise TransitionDenied("guardian_denied")
    except TransitionDenied:
        raise
    except Exception as exc:
        raise TransitionDenied("guardian_unavailable") from exc

    try:
        case = load_trusted_case(case_id)
    except Exception as exc:
        raise TransitionDenied("case_unavailable") from exc
    if not isinstance(case, DebtCase) or case.case_id != case_id:
        raise TransitionDenied("case_unavailable")
    updated, receipt = transition(
        case, action, authenticated_identity_id=principal,
        expected_version=expected_version, evidence_ref=evidence_ref,
    )
    return PendingDebtChange(updated, receipt)
