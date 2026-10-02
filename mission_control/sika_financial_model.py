"""SIKA financial operating model.

This module defines the human-facing SIKA domains and the non-negotiable
separation between canonical value, treasury, custody and recognition state.
It creates no bank account, custody service, investment product or payment rail.
"""
from __future__ import annotations

from dataclasses import dataclass

FRONT_DOORS: tuple[dict[str, object], ...] = (
    {
        "id": "everyday",
        "name": "Everyday",
        "purpose": "Daily value visibility and approved payment handoff.",
        "regulated_capability": "payments",
        "execution_enabled": False,
    },
    {
        "id": "business",
        "name": "Business",
        "purpose": "Business value, invoices, expenses and operating controls.",
        "regulated_capability": "payments",
        "execution_enabled": False,
    },
    {
        "id": "treasury",
        "name": "Treasury",
        "purpose": "Liquidity, reserves, obligations and settlement oversight.",
        "regulated_capability": "payments_fx",
        "execution_enabled": False,
    },
    {
        "id": "vault",
        "name": "Vault",
        "purpose": "Custody-facing asset inventory and evidence boundaries.",
        "regulated_capability": "custody",
        "execution_enabled": False,
    },
    {
        "id": "wealth",
        "name": "Wealth",
        "purpose": "Wealth overview and advisory handoff without execution.",
        "regulated_capability": "investments_advice",
        "execution_enabled": False,
    },
    {
        "id": "legacy",
        "name": "Legacy",
        "purpose": "Long-term ownership, succession and evidence planning.",
        "regulated_capability": "legal_wealth",
        "execution_enabled": False,
    },
    {
        "id": "global",
        "name": "Global",
        "purpose": "Cross-border value, FX quotation and settlement visibility.",
        "regulated_capability": "payments_fx",
        "execution_enabled": False,
    },
)

LEDGER_CLASSES: tuple[dict[str, object], ...] = (
    {
        "id": "canonical_value",
        "owner": "SIKA Core",
        "meaning": "Canonical SIKA value record.",
        "spendable_claim": False,
        "custody_claim": False,
    },
    {
        "id": "treasury",
        "owner": "SIKA Treasury",
        "meaning": "Treasury allocation, obligation and liquidity state.",
        "spendable_claim": False,
        "custody_claim": False,
    },
    {
        "id": "custody",
        "owner": "SIKA Vault",
        "meaning": "Asset custody inventory and evidence references.",
        "spendable_claim": False,
        "custody_claim": True,
    },
    {
        "id": "recognition",
        "owner": "OAP Recognition",
        "meaning": "Contribution and recognition state; never cash-equivalent.",
        "spendable_claim": False,
        "custody_claim": False,
    },
)


class OperatingModelError(ValueError):
    """Raised when SIKA financial-domain separation is violated."""


@dataclass(frozen=True)
class BalanceReference:
    ledger_class: str
    amount_reference: str
    spendable: bool
    money_claim: bool
    custody_claim: bool


def _by_id(items: tuple[dict[str, object], ...]) -> dict[str, dict[str, object]]:
    return {str(item["id"]): item for item in items}


def validate_model() -> dict[str, object]:
    doors = _by_id(FRONT_DOORS)
    ledgers = _by_id(LEDGER_CLASSES)
    errors: list[str] = []

    if len(doors) != len(FRONT_DOORS):
        errors.append("front_door_ids_must_be_unique")
    if len(ledgers) != len(LEDGER_CLASSES):
        errors.append("ledger_class_ids_must_be_unique")

    required_doors = {
        "everyday",
        "business",
        "treasury",
        "vault",
        "wealth",
        "legacy",
        "global",
    }
    if set(doors) != required_doors:
        errors.append("seven_sika_front_doors_required")

    if any(bool(item["execution_enabled"]) for item in FRONT_DOORS):
        errors.append("regulated_execution_must_default_closed")

    recognition = ledgers.get("recognition")
    if recognition and (
        recognition["spendable_claim"] or recognition["custody_claim"]
    ):
        errors.append("recognition_must_not_be_money_or_custody")

    custody = ledgers.get("custody")
    if custody and not custody["custody_claim"]:
        errors.append("custody_class_must_be_explicit")

    owners = [str(item["owner"]) for item in LEDGER_CLASSES]
    if len(owners) != len(set(owners)):
        errors.append("ledger_classes_must_have_distinct_owners")

    return {
        "passed": not errors,
        "errors": tuple(errors),
        "front_doors": len(FRONT_DOORS),
        "ledger_classes": len(LEDGER_CLASSES),
        "regulated_execution_enabled": False,
        "human_authority_final": True,
    }


def balance_reference(ledger_class: str, amount_reference: object) -> BalanceReference:
    classes = _by_id(LEDGER_CLASSES)
    key = str(ledger_class or "").strip().casefold()
    if key not in classes:
        raise OperatingModelError("unknown_ledger_class")
    amount = str(amount_reference or "").strip()
    if not amount:
        raise OperatingModelError("amount_reference_required")

    item = classes[key]
    return BalanceReference(
        ledger_class=key,
        amount_reference=amount[:120],
        spendable=False,
        money_claim=False,
        custody_claim=bool(item["custody_claim"]),
    )


def status() -> dict[str, object]:
    validation = validate_model()
    return {
        "system": "SIKA Financial Operating Model",
        "architecture": (
            "Everyday · Business · Treasury · Vault · Wealth · Legacy · Global"
        ),
        "front_doors": FRONT_DOORS,
        "ledger_classes": LEDGER_CLASSES,
        "separation_rules": (
            "Canonical value is not automatically spendable bank money.",
            "Treasury state is separate from personal or business value.",
            "Custody inventory is not a cash balance.",
            "Recognition is not money, custody or treasury state.",
            "FX and settlement occur only through governed provider boundaries.",
        ),
        "validation": validation,
        "provider_adapter_required": True,
        "regulated_execution_enabled": False,
        "customer_funds_enabled": False,
        "investment_execution_enabled": False,
        "custody_execution_enabled": False,
        "human_authority_final": True,
    }
