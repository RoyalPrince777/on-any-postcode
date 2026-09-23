"""Isolated, non-executing OAP Debt Truth contract.

No authentication, data storage, HRM, creditor, payment, migration or HTTP route
is implemented here. This module cannot verify a legal debt discharge.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import re

_SAFE_REF = re.compile(r"[A-Za-z0-9_-]{8,64}\Z")


class CasePhase(str, Enum):
    OPEN = "OPEN"
    PAUSED = "PAUSED"
    CLOSED = "CLOSED"
    STOPPED = "STOPPED"


class Action(str, Enum):
    RECORD_DOCUMENT = "RECORD_DOCUMENT"
    DISPUTE = "DISPUTE"
    IDENTIFY_SUPPORT = "IDENTIFY_SUPPORT"
    RECORD_OUTCOME = "RECORD_OUTCOME"
    PAUSE = "PAUSE"
    RESUME = "RESUME"
    CLOSE = "CLOSE"
    REOPEN = "REOPEN"
    STOP = "STOP"
    VERIFY_OUTCOME = "VERIFY_OUTCOME"  # unsupported without independent authority
    CONTACT_CREDITOR = "CONTACT_CREDITOR"
    MAKE_PAYMENT = "MAKE_PAYMENT"
    SETTLE_DEBT = "SETTLE_DEBT"
    ERASE_OBLIGATION = "ERASE_OBLIGATION"


class TransitionDenied(ValueError):
    """Generic denial: never include personal or financial content."""


@dataclass(frozen=True, slots=True)
class DebtCase:
    case_id: str
    owner_id: str
    phase: CasePhase = CasePhase.OPEN
    version: int = 0
    documented: bool = False
    disputed: bool = False
    support_identified: bool = False
    outcome_recorded: bool = False
    outcome_verified: bool = False
    debt_discharged: bool = False

    def __post_init__(self) -> None:
        _validate_case(self)


def _validate_case(case: DebtCase) -> None:
    if not isinstance(case, DebtCase):
        raise TransitionDenied("invalid_case")
    if (
        not isinstance(case.case_id, str)
        or not _SAFE_REF.fullmatch(case.case_id)
        or not isinstance(case.owner_id, str)
        or not _SAFE_REF.fullmatch(case.owner_id)
        or not isinstance(case.phase, CasePhase)
        or type(case.version) is not int
        or case.version < 0
    ):
        raise TransitionDenied("invalid_case")
    flags = (
        case.documented,
        case.disputed,
        case.support_identified,
        case.outcome_recorded,
        case.outcome_verified,
        case.debt_discharged,
    )
    if any(type(flag) is not bool for flag in flags):
        raise TransitionDenied("invalid_case")
    if case.outcome_verified or case.debt_discharged:
        raise TransitionDenied("unsupported_financial_claim")
    if case.version == 0 and (any(flags) or case.phase is not CasePhase.OPEN):
        raise TransitionDenied("invalid_case")


@dataclass(frozen=True, slots=True)
class ChangeReceipt:
    case_id: str
    version: int
    event: str
    # No amounts, names, documents, creditor IDs or account identifiers.


def new_case(case_id: str, owner_id: str) -> DebtCase:
    if (
        not isinstance(case_id, str)
        or not isinstance(owner_id, str)
        or not _SAFE_REF.fullmatch(case_id)
        or not _SAFE_REF.fullmatch(owner_id)
    ):
        raise TransitionDenied("invalid_reference")
    return DebtCase(case_id=case_id, owner_id=owner_id)


def transition(
    case: DebtCase,
    action: Action,
    *,
    authenticated_identity_id: str,
    expected_version: int,
    evidence_ref: str | None = None,
) -> tuple[DebtCase, ChangeReceipt]:
    """Return proposed case and minimal receipt; make no persistent changes."""
    _validate_case(case)
    if not authenticated_identity_id or authenticated_identity_id != case.owner_id:
        raise TransitionDenied("access_denied")
    if type(expected_version) is not int or expected_version != case.version:
        raise TransitionDenied("stale_case_version")
    if not isinstance(action, Action):
        raise TransitionDenied("unknown_action")
    if action in {
        Action.VERIFY_OUTCOME, Action.CONTACT_CREDITOR, Action.MAKE_PAYMENT,
        Action.SETTLE_DEBT, Action.ERASE_OBLIGATION,
    }:
        raise TransitionDenied("action_not_supported")

    updates: dict[str, object] = {}
    if action is Action.STOP:
        if case.phase is CasePhase.STOPPED:
            raise TransitionDenied("invalid_phase")
        updates["phase"] = CasePhase.STOPPED
    elif action is Action.REOPEN:
        if case.phase not in {CasePhase.CLOSED, CasePhase.STOPPED}:
            raise TransitionDenied("invalid_phase")
        updates["phase"] = CasePhase.OPEN
    elif action is Action.RESUME:
        if case.phase is not CasePhase.PAUSED:
            raise TransitionDenied("invalid_phase")
        updates["phase"] = CasePhase.OPEN
    elif action is Action.PAUSE:
        if case.phase is not CasePhase.OPEN:
            raise TransitionDenied("invalid_phase")
        updates["phase"] = CasePhase.PAUSED
    elif action is Action.CLOSE:
        if case.phase not in {CasePhase.OPEN, CasePhase.PAUSED}:
            raise TransitionDenied("invalid_phase")
        updates["phase"] = CasePhase.CLOSED
    else:
        if case.phase is not CasePhase.OPEN:
            raise TransitionDenied("invalid_phase")
        if not isinstance(evidence_ref, str) or not _SAFE_REF.fullmatch(evidence_ref):
            raise TransitionDenied("invalid_reference")
        target = {
            Action.RECORD_DOCUMENT: "documented",
            Action.DISPUTE: "disputed",
            Action.IDENTIFY_SUPPORT: "support_identified",
            Action.RECORD_OUTCOME: "outcome_recorded",
        }.get(action)
        if target is None:
            raise TransitionDenied("action_not_supported")
        if getattr(case, target):
            raise TransitionDenied("duplicate_event")
        updates[target] = True
        # Opaque references are not self-authenticating evidence; no document
        # content or reference is persisted by this evaluator.
    updated = replace(case, **updates, version=case.version + 1)
    return updated, ChangeReceipt(case.case_id, updated.version, action.value)
