"""First-party OAP Fashion draft specifications, with no supplier or money side effects.

This isolated domain module complements the existing Market products and
Commerce Core; it neither replaces tables nor creates a production order.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from enum import Enum
from uuid import UUID


class FashionError(ValueError):
    """A Fashion ownership, rights or lifecycle gate failed."""


class FashionState(str, Enum):
    DRAFT = "DRAFT"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    APPROVED = "APPROVED"
    STOPPED = "STOPPED"


_CURRENCY = re.compile(r"^[A-Z]{3}$")
_SKU = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,79}$")
_TYPES = frozenset({"tshirt", "hoodie", "jacket", "tracksuit", "polo",
                    "shirt", "cargo", "shorts", "joggers", "hat", "bag",
                    "accessory", "other"})


def identity(value: object) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise FashionError("invalid_identity") from exc


def minor_units(value: object) -> int:
    if isinstance(value, bool):
        raise FashionError("invalid_price")
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise FashionError("invalid_price") from exc
    if not amount.is_finite() or amount < 0 or amount != amount.to_integral_value():
        raise FashionError("invalid_price")
    return int(amount)


@dataclass(frozen=True)
class FashionVariant:
    sku: str
    size: str
    colour: str
    price_minor: int
    currency: str = "GBP"

    def __post_init__(self) -> None:
        if not _SKU.fullmatch(self.sku):
            raise FashionError("invalid_sku")
        if not self.size.strip() or not self.colour.strip():
            raise FashionError("variant_details_required")
        minor_units(self.price_minor)
        if not _CURRENCY.fullmatch(self.currency):
            raise FashionError("invalid_currency")


@dataclass
class FashionDraft:
    """Owner-scoped catalogue metadata; actual files stay in existing OAP media."""
    owner_identity_id: str
    product_id: str
    name: str
    product_type: str
    artwork_ref: str
    artwork_rights_confirmed: bool
    merchant_certified: bool
    variants: tuple[FashionVariant, ...]
    state: FashionState = FashionState.DRAFT
    events: list[tuple[str, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        identity(self.owner_identity_id)
        identity(self.product_id)
        if not self.name.strip() or not self.artwork_ref.strip():
            raise FashionError("product_or_artwork_required")
        if self.product_type not in _TYPES:
            raise FashionError("invalid_product_type")
        if not self.variants or len({v.sku for v in self.variants}) != len(self.variants):
            raise FashionError("variants_required_or_duplicate_sku")

    def _owner(self, actor: object) -> None:
        if identity(actor) != identity(self.owner_identity_id):
            raise FashionError("not_product_owner")

    def submit_review(self, actor: object, evidence_ref: str) -> None:
        self._owner(actor)
        if self.state != FashionState.DRAFT:
            raise FashionError("invalid_state")
        if not self.merchant_certified:
            raise FashionError("certified_merchant_required")
        if not self.artwork_rights_confirmed:
            raise FashionError("artwork_rights_required")
        if not isinstance(evidence_ref, str) or not evidence_ref.strip():
            raise FashionError("review_evidence_required")
        self.events.append((FashionState.READY_FOR_REVIEW.value, evidence_ref))
        self.state = FashionState.READY_FOR_REVIEW

    def approve(self, actor: object, evidence_ref: str, *, human_approval: bool) -> None:
        self._owner(actor)
        if self.state != FashionState.READY_FOR_REVIEW:
            raise FashionError("invalid_state")
        if human_approval is not True:
            raise FashionError("human_approval_required")
        if not isinstance(evidence_ref, str) or not evidence_ref.strip():
            raise FashionError("approval_evidence_required")
        self.events.append((FashionState.APPROVED.value, evidence_ref))
        self.state = FashionState.APPROVED

    def stop(self, actor: object, reason: str) -> None:
        self._owner(actor)
        if self.state == FashionState.STOPPED:
            raise FashionError("already_stopped")
        if not isinstance(reason, str) or not reason.strip():
            raise FashionError("stop_reason_required")
        self.events.append((FashionState.STOPPED.value, reason))
        self.state = FashionState.STOPPED

    def market_projection(self, actor: object) -> dict[str, object]:
        """A safe catalogue projection, NOT publication or stock availability."""
        self._owner(actor)
        if self.state != FashionState.APPROVED:
            raise FashionError("product_not_approved")
        return {
            "owner_identity_id": self.owner_identity_id,
            "product_id": self.product_id,
            "name": self.name,
            "product_type": self.product_type,
            "artwork_ref": self.artwork_ref,
            "variants": tuple({
                "sku": v.sku, "size": v.size, "colour": v.colour,
                "price_minor": v.price_minor, "currency": v.currency,
            } for v in self.variants),
            "publication_performed": False,
            "stock_confirmed": False,
            "payment_performed": False,
            "manufacturing_order_performed": False,
            "external_supplier_required": False,
        }
