"""Read-only intercompany accounting intelligence for SIKA.

Matches due-to/due-from balances between separate OAP banking entities and
produces elimination evidence. It does not pool funds, settle balances,
collapse legal entities, or move money.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


class IntercompanyAccountingError(ValueError):
    """Raised when intercompany evidence is invalid."""


def _required(value: object, *, error: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise IntercompanyAccountingError(error)
    return text


def _amount(value: object, *, error: str) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise IntercompanyAccountingError(error) from exc
    if not parsed.is_finite() or parsed < 0:
        raise IntercompanyAccountingError(error)
    return parsed.quantize(Decimal("0.01"))


@dataclass(frozen=True)
class IntercompanyPosition:
    entity_id: str
    counterparty_entity_id: str
    jurisdiction: str
    counterparty_jurisdiction: str
    currency: str
    due_from: Decimal
    due_to: Decimal
    reference: str


@dataclass(frozen=True)
class IntercompanyMatch:
    reference: str
    currency: str
    entity_a: str
    entity_b: str
    jurisdiction_a: str
    jurisdiction_b: str
    due_from_a: Decimal
    due_to_b: Decimal
    matched_amount: Decimal
    difference: Decimal
    state: str
    elimination_ready: bool
    cross_jurisdiction: bool
    money_pooled: bool = False
    settlement_executed: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "reference": self.reference,
            "currency": self.currency,
            "entity_a": self.entity_a,
            "entity_b": self.entity_b,
            "jurisdiction_a": self.jurisdiction_a,
            "jurisdiction_b": self.jurisdiction_b,
            "due_from_a": f"{self.due_from_a:.2f}",
            "due_to_b": f"{self.due_to_b:.2f}",
            "matched_amount": f"{self.matched_amount:.2f}",
            "difference": f"{self.difference:.2f}",
            "state": self.state,
            "elimination_ready": self.elimination_ready,
            "cross_jurisdiction": self.cross_jurisdiction,
            "money_pooled": self.money_pooled,
            "settlement_executed": self.settlement_executed,
        }


def position(
    *,
    entity_id: object,
    counterparty_entity_id: object,
    jurisdiction: object,
    counterparty_jurisdiction: object,
    currency: object,
    due_from: object = "0",
    due_to: object = "0",
    reference: object,
) -> IntercompanyPosition:
    entity = _required(entity_id, error="entity_id_required")
    counterparty = _required(
        counterparty_entity_id,
        error="counterparty_entity_id_required",
    )
    if entity == counterparty:
        raise IntercompanyAccountingError("entities_must_differ")
    return IntercompanyPosition(
        entity_id=entity,
        counterparty_entity_id=counterparty,
        jurisdiction=_required(
            jurisdiction,
            error="jurisdiction_required",
        ),
        counterparty_jurisdiction=_required(
            counterparty_jurisdiction,
            error="counterparty_jurisdiction_required",
        ),
        currency=_required(currency, error="currency_required").upper(),
        due_from=_amount(due_from, error="due_from_invalid"),
        due_to=_amount(due_to, error="due_to_invalid"),
        reference=_required(reference, error="reference_required"),
    )


def match(
    *,
    left: IntercompanyPosition,
    right: IntercompanyPosition,
) -> IntercompanyMatch:
    if left.entity_id != right.counterparty_entity_id:
        raise IntercompanyAccountingError("entity_pair_mismatch")
    if left.counterparty_entity_id != right.entity_id:
        raise IntercompanyAccountingError("entity_pair_mismatch")
    if left.reference != right.reference:
        raise IntercompanyAccountingError("reference_mismatch")
    if left.currency != right.currency:
        raise IntercompanyAccountingError("currency_mismatch")
    if left.jurisdiction != right.counterparty_jurisdiction:
        raise IntercompanyAccountingError("jurisdiction_pair_mismatch")
    if left.counterparty_jurisdiction != right.jurisdiction:
        raise IntercompanyAccountingError("jurisdiction_pair_mismatch")

    matched = min(left.due_from, right.due_to)
    difference = (left.due_from - right.due_to).copy_abs()
    state = "MATCHED" if difference == 0 else "MISMATCH"
    return IntercompanyMatch(
        reference=left.reference,
        currency=left.currency,
        entity_a=left.entity_id,
        entity_b=right.entity_id,
        jurisdiction_a=left.jurisdiction,
        jurisdiction_b=right.jurisdiction,
        due_from_a=left.due_from,
        due_to_b=right.due_to,
        matched_amount=matched,
        difference=difference,
        state=state,
        elimination_ready=state == "MATCHED",
        cross_jurisdiction=left.jurisdiction != right.jurisdiction,
        money_pooled=False,
        settlement_executed=False,
    )


def status() -> dict[str, object]:
    return {
        "system": "SIKA Intercompany Accounting",
        "first_party": True,
        "mode": "read_only_match_and_elimination_evidence",
        "due_to_due_from_matching": True,
        "jurisdiction_isolation": True,
        "elimination_evidence": True,
        "legal_entities_collapsed": False,
        "cross_jurisdiction_money_pooling": False,
        "settlement_execution": False,
        "money_movement": False,
        "human_authority_final": True,
    }
