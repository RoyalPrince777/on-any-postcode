"""Canonical OAP action-risk router.

This module classifies a requested action before any execution layer is reached.
It never executes, approves, spends, publishes, deletes, changes permissions, or
grants authority. Its job is to choose the smallest safe governance path.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

ROUTE_DIRECT_ANSWER: Final = "DIRECT_ANSWER"
ROUTE_PREPARE: Final = "PREPARE"
ROUTE_CONFIRM: Final = "CONFIRM"
ROUTE_GOVERNANCE: Final = "GOVERNANCE"
ROUTE_BLOCK: Final = "BLOCK"

ROUTES: Final = (
    ROUTE_DIRECT_ANSWER,
    ROUTE_PREPARE,
    ROUTE_CONFIRM,
    ROUTE_GOVERNANCE,
    ROUTE_BLOCK,
)

_HIGH_IMPACT_TERMS: Final = (
    "permission",
    "role",
    "admin",
    "owner",
    "founder",
    "governance",
    "constitution",
    "security policy",
    "disable security",
    "bypass",
    "production",
    "deploy",
    "database migration",
    "banking",
    "settlement",
    "compliance",
)

_VALUE_TRANSFER_TERMS: Final = (
    "pay",
    "payment",
    "send money",
    "transfer",
    "purchase",
    "buy",
    "refund",
    "sika",
)

_EXTERNAL_EFFECT_TERMS: Final = (
    "send",
    "publish",
    "post",
    "message",
    "email",
    "call",
    "book",
    "reserve",
    "order",
    "delete",
    "remove",
    "cancel",
    "update",
    "change",
    "create",
)

_BLOCKED_TERMS: Final = (
    "self approve",
    "self-approve",
    "skip guardian",
    "skip confirmation",
    "bypass guardian",
    "bypass green gate",
    "disable audit",
    "fake green",
)


@dataclass(frozen=True)
class ActionRiskDecision:
    route: str
    risk_level: str
    smi_depth: int
    confirmation_required: bool
    guardian_required: bool
    red_team_required: bool
    founder_final_required: bool
    execution_allowed_by_router: bool
    reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "route": self.route,
            "risk_level": self.risk_level,
            "smi_depth": self.smi_depth,
            "confirmation_required": self.confirmation_required,
            "guardian_required": self.guardian_required,
            "red_team_required": self.red_team_required,
            "founder_final_required": self.founder_final_required,
            "execution_allowed_by_router": self.execution_allowed_by_router,
            "reasons": self.reasons,
            "human_authority_final": True,
        }


def _contains_term(text: str, term: str) -> bool:
    """Match canonical words/phrases without substring collisions."""

    pattern = r"(?<!\\w)" + re.escape(term) + r"(?!\\w)"
    return re.search(pattern, text) is not None


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(_contains_term(text, term) for term in terms)


_INFORMATIONAL_PREFIXES: Final = (
    "what is ",
    "what's ",
    "what are ",
    "explain ",
    "describe ",
    "define ",
    "tell me about ",
    "how does ",
    "how do ",
    "why ",
)


def _is_informational(text: str) -> bool:
    stripped = text.lstrip()
    return any(stripped.startswith(prefix) for prefix in _INFORMATIONAL_PREFIXES)


def _has_action_intent(text: str, *, asks_to_execute: bool) -> bool:
    if asks_to_execute:
        return True
    if _is_informational(text):
        return False
    return _contains_any(
        text,
        tuple(dict.fromkeys((*_EXTERNAL_EFFECT_TERMS, "deploy", "migrate", "disable", "bypass"))),
    )


def route_action(
    request: str,
    *,
    asks_to_execute: bool = False,
    external_effect: bool | None = None,
    reversible: bool = True,
    value_transfer: bool | None = None,
    authority_change: bool | None = None,
    privacy_sensitive: bool = False,
    safety_critical: bool = False,
) -> ActionRiskDecision:
    """Classify one request into the smallest safe OAP governance path.

    The router is deliberately non-executing. execution_allowed_by_router is
    always False; a later, separately governed execution layer must validate
    identity, permissions, receipts, and any required confirmation or approval.
    """

    text = str(request or "").strip().casefold()
    if not text:
        return ActionRiskDecision(
            route=ROUTE_PREPARE,
            risk_level="LOW",
            smi_depth=3,
            confirmation_required=False,
            guardian_required=False,
            red_team_required=False,
            founder_final_required=False,
            execution_allowed_by_router=False,
            reasons=("Empty or ambiguous request; prepare clarification without side effects.",),
        )

    informational = _is_informational(text)
    bypass_request = bool(
        not informational and _contains_any(text, _BLOCKED_TERMS)
    )
    action_intent = bool(
        bypass_request
        or _has_action_intent(text, asks_to_execute=asks_to_execute)
    )
    inferred_external = bool(action_intent and _contains_any(text, _EXTERNAL_EFFECT_TERMS))
    inferred_value = bool(action_intent and _contains_any(text, _VALUE_TRANSFER_TERMS))
    inferred_authority = bool(action_intent and _contains_any(text, _HIGH_IMPACT_TERMS))

    external = inferred_external if external_effect is None else bool(external_effect)
    money = inferred_value if value_transfer is None else bool(value_transfer)
    authority = inferred_authority if authority_change is None else bool(authority_change)

    if bypass_request:
        return ActionRiskDecision(
            route=ROUTE_BLOCK,
            risk_level="CRITICAL",
            smi_depth=21,
            confirmation_required=False,
            guardian_required=True,
            red_team_required=True,
            founder_final_required=True,
            execution_allowed_by_router=False,
            reasons=("Request attempts to bypass a locked governance or evidence boundary.",),
        )

    reasons: list[str] = []
    if safety_critical:
        reasons.append("Safety-critical action.")
    if authority:
        reasons.append("Authority, governance, production, security, or compliance boundary.")
    if money:
        reasons.append("Value transfer or payment-related effect.")
    if privacy_sensitive:
        reasons.append("Private or sensitive OAP Data involved.")
    if external:
        reasons.append("Action can change external state.")
    if not reversible:
        reasons.append("Action is not safely reversible.")

    if safety_critical or authority:
        return ActionRiskDecision(
            route=ROUTE_GOVERNANCE,
            risk_level="CRITICAL" if safety_critical else "HIGH",
            smi_depth=21,
            confirmation_required=True,
            guardian_required=True,
            red_team_required=True,
            founder_final_required=True,
            execution_allowed_by_router=False,
            reasons=tuple(reasons) or ("Consequential governance review required.",),
        )

    if money or (external and (privacy_sensitive or not reversible)):
        return ActionRiskDecision(
            route=ROUTE_CONFIRM,
            risk_level="HIGH",
            smi_depth=21 if money or not reversible else 7,
            confirmation_required=True,
            guardian_required=True,
            red_team_required=bool(money or not reversible),
            founder_final_required=False,
            execution_allowed_by_router=False,
            reasons=tuple(reasons),
        )

    if asks_to_execute and external:
        return ActionRiskDecision(
            route=ROUTE_CONFIRM,
            risk_level="MEDIUM",
            smi_depth=7,
            confirmation_required=True,
            guardian_required=True,
            red_team_required=False,
            founder_final_required=False,
            execution_allowed_by_router=False,
            reasons=tuple(reasons) or ("User requested an external side effect.",),
        )

    if external:
        return ActionRiskDecision(
            route=ROUTE_PREPARE,
            risk_level="MEDIUM",
            smi_depth=7,
            confirmation_required=False,
            guardian_required=True,
            red_team_required=False,
            founder_final_required=False,
            execution_allowed_by_router=False,
            reasons=tuple(reasons) or ("Prepare the action without causing the side effect.",),
        )

    return ActionRiskDecision(
        route=ROUTE_DIRECT_ANSWER,
        risk_level="LOW",
        smi_depth=3,
        confirmation_required=False,
        guardian_required=False,
        red_team_required=False,
        founder_final_required=False,
        execution_allowed_by_router=False,
        reasons=("Read-only or informational request; no external side effect detected.",),
    )


def status() -> dict[str, object]:
    return {
        "component": "OAP Action Risk Router",
        "routes": ROUTES,
        "ready": True,
        "provider_neutral": True,
        "first_party_policy": True,
        "executes_actions": False,
        "self_approval_allowed": False,
        "human_authority_final": True,
        "rule": "Answer directly when safe; prepare before acting; confirm side effects; escalate high-impact changes; block governance bypass.",
    }
