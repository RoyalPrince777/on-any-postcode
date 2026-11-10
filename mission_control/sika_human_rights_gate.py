"""Deterministic SIKA Human Rights Gate.

This gate reviews consequential SIKA restrictions before they may enter human
financial review. It does not create legal rights, decide legal entitlement,
override applicable law, execute financial actions, or move money.
"""
from __future__ import annotations

from dataclasses import dataclass

CONSEQUENTIAL_ACTIONS = frozenset(
    {
        "ACCOUNT_FREEZE",
        "ACCOUNT_CLOSE",
        "PAYMENT_RESTRICTION",
        "CARD_FREEZE",
        "FRAUD_ESCALATION",
        "DISPUTE_RESOLUTION",
    }
)

RIGHTS_PRINCIPLES = (
    "human_dignity",
    "non_discrimination",
    "privacy",
    "accessibility",
    "evidence_before_restriction",
    "explanation",
    "remedy_and_appeal",
    "human_authority",
)


class HumanRightsGateError(ValueError):
    """Raised when a rights-review request is malformed."""


def _required(value: object, *, error: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise HumanRightsGateError(error)
    return text


@dataclass(frozen=True)
class HumanRightsReview:
    action_type: str
    subject_reference: str
    evidence_reference: str
    reason_code: str
    privacy_minimised: bool
    non_discrimination_reviewed: bool
    accessibility_considered: bool
    explanation_available: bool
    remedy_available: bool
    human_review_required: bool
    state: str
    may_enter_human_financial_review: bool
    money_moved: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "action_type": self.action_type,
            "subject_reference": self.subject_reference,
            "evidence_reference": self.evidence_reference,
            "reason_code": self.reason_code,
            "privacy_minimised": self.privacy_minimised,
            "non_discrimination_reviewed": self.non_discrimination_reviewed,
            "accessibility_considered": self.accessibility_considered,
            "explanation_available": self.explanation_available,
            "remedy_available": self.remedy_available,
            "human_review_required": self.human_review_required,
            "state": self.state,
            "may_enter_human_financial_review": (
                self.may_enter_human_financial_review
            ),
            "money_moved": self.money_moved,
        }


def review(
    *,
    action_type: object,
    subject_reference: object,
    evidence_reference: object,
    reason_code: object,
    privacy_minimised: bool,
    non_discrimination_reviewed: bool,
    accessibility_considered: bool,
    explanation_available: bool,
    remedy_available: bool,
) -> HumanRightsReview:
    """Fail closed unless every rights-control requirement is evidenced."""

    action = _required(action_type, error="action_type_required").upper()
    if action not in CONSEQUENTIAL_ACTIONS:
        raise HumanRightsGateError("unsupported_consequential_action")

    subject = _required(subject_reference, error="subject_reference_required")
    evidence = _required(evidence_reference, error="evidence_reference_required")
    reason = _required(reason_code, error="reason_code_required")

    checks = (
        privacy_minimised,
        non_discrimination_reviewed,
        accessibility_considered,
        explanation_available,
        remedy_available,
    )
    passed = all(checks)
    return HumanRightsReview(
        action_type=action,
        subject_reference=subject,
        evidence_reference=evidence,
        reason_code=reason,
        privacy_minimised=bool(privacy_minimised),
        non_discrimination_reviewed=bool(non_discrimination_reviewed),
        accessibility_considered=bool(accessibility_considered),
        explanation_available=bool(explanation_available),
        remedy_available=bool(remedy_available),
        human_review_required=True,
        state="PASS_TO_HUMAN_REVIEW" if passed else "HOLD",
        may_enter_human_financial_review=passed,
        money_moved=False,
    )


def status() -> dict[str, object]:
    return {
        "system": "SIKA Human Rights Gate",
        "first_party": True,
        "mode": "deterministic_fail_closed_review",
        "principles": list(RIGHTS_PRINCIPLES),
        "consequential_actions": sorted(CONSEQUENTIAL_ACTIONS),
        "evidence_required": True,
        "reason_required": True,
        "privacy_minimisation_required": True,
        "non_discrimination_review_required": True,
        "accessibility_consideration_required": True,
        "explanation_path_required": True,
        "remedy_path_required": True,
        "human_review_required": True,
        "creates_legal_entitlement": False,
        "overrides_applicable_law": False,
        "automated_punishment": False,
        "financial_execution": False,
        "money_movement": False,
        "human_authority_final": True,
    }
