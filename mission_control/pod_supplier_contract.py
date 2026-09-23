"""OAP-owned print-on-demand supplier contracts, with no external execution.

Mind: strict owner- and merchant-scoped catalogue/supplier eligibility.
Body: approved quote and isolated supplier handoff preparation.
Soul: STOP, idempotency, receipt verification, and recovery.
All state is caller-owned: this module never connects to a supplier, database,
payment rail, production queue, or customer notification service.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Mapping
from uuid import UUID


class PODState(str, Enum):
    DRAFT = "DRAFT"
    QUOTED = "QUOTED"
    APPROVED = "APPROVED"
    SUBMITTED = "SUBMITTED"
    ACCEPTED = "ACCEPTED"
    STOPPED = "STOPPED"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"


class PODContractError(ValueError):
    """Fail-closed supplier or order contract violation."""


def _uuid(value: str, label: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise PODContractError(f"invalid_{label}") from exc


def _money(value: object, label: str) -> int:
    if isinstance(value, bool):
        raise PODContractError(f"invalid_{label}")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise PODContractError(f"invalid_{label}") from exc
    if not result.is_finite() or result < 0 or result != result.to_integral_value():
        raise PODContractError(f"invalid_{label}")
    return int(result)


@dataclass(frozen=True)
class Supplier:
    supplier_id: str
    display_name: str
    approved: bool
    supported_product_types: frozenset[str]
    supported_countries: frozenset[str]
    multi_merchant_authorised: bool = False
    external_execution_enabled: bool = False

    def __post_init__(self) -> None:
        _uuid(self.supplier_id, "supplier_id")
        if not self.display_name.strip() or not self.supported_product_types or not self.supported_countries:
            raise PODContractError("incomplete_supplier_contract")
        if self.external_execution_enabled:
            raise PODContractError("external_execution_not_supported")


@dataclass(frozen=True)
class PODOrder:
    order_id: str
    seller_id: str
    buyer_id: str
    product_id: str
    product_type: str
    destination_country: str
    quantity: int
    artwork_ref: str
    artwork_rights_confirmed: bool
    certified_merchant: bool
    fulfilment_intent_exists: bool

    def __post_init__(self) -> None:
        for name in ("order_id", "seller_id", "buyer_id", "product_id"):
            _uuid(getattr(self, name), name)
        if self.seller_id == self.buyer_id or type(self.quantity) is not int or not 1 <= self.quantity <= 99:
            raise PODContractError("invalid_order_participants_or_quantity")
        if not self.product_type or not self.destination_country or not self.artwork_ref.strip():
            raise PODContractError("incomplete_product_specification")


@dataclass(frozen=True)
class Quote:
    supplier_id: str
    variant_id: str
    amount_minor: int
    shipping_minor: int
    currency: str
    evidence_ref: str
    country: str
    product_type: str
    quantity: int

    def __post_init__(self) -> None:
        _uuid(self.supplier_id, "supplier_id")
        _money(self.amount_minor, "amount_minor")
        _money(self.shipping_minor, "shipping_minor")
        if not self.variant_id.strip() or not self.evidence_ref.strip() or len(self.currency) != 3:
            raise PODContractError("incomplete_quote")
        if type(self.quantity) is not int or self.quantity < 1:
            raise PODContractError("invalid_quote_quantity")


@dataclass
class PODIntent:
    order: PODOrder
    supplier: Supplier
    quote: Quote
    idempotency_key: str
    state: PODState = PODState.DRAFT
    approved_by: str | None = None
    submission_reference: str | None = None
    receipt_reference: str | None = None
    events: list[tuple[str, str]] = field(default_factory=list)

    def _event(self, state: PODState, evidence: str) -> None:
        if not evidence.strip():
            raise PODContractError("evidence_required")
        self.state = state
        self.events.append((state.value, evidence))

    def quote_ready(self, actor_id: str) -> None:
        if self.state != PODState.DRAFT:
            raise PODContractError("invalid_state")
        if _uuid(actor_id, "actor_id") != _uuid(self.order.seller_id, "seller_id"):
            raise PODContractError("seller_not_owned")
        if not self.order.certified_merchant or not self.order.fulfilment_intent_exists:
            raise PODContractError("merchant_or_fulfilment_gate")
        if not self.order.artwork_rights_confirmed:
            raise PODContractError("artwork_rights_unconfirmed")
        if not self.supplier.approved or not self.supplier.multi_merchant_authorised:
            raise PODContractError("supplier_not_authorised_for_platform")
        if (self.order.product_type not in self.supplier.supported_product_types
                or self.order.destination_country not in self.supplier.supported_countries):
            raise PODContractError("supplier_cannot_fulfil_order")
        if (_uuid(self.quote.supplier_id, "supplier_id") != _uuid(self.supplier.supplier_id, "supplier_id")
                or self.quote.country != self.order.destination_country
                or self.quote.product_type != self.order.product_type
                or self.quote.quantity != self.order.quantity):
            raise PODContractError("quote_order_mismatch")
        if not isinstance(self.idempotency_key, str) or not 8 <= len(self.idempotency_key) <= 160:
            raise PODContractError("invalid_idempotency_key")
        self._event(PODState.QUOTED, self.quote.evidence_ref)

    def approve(self, actor_id: str, approval_ref: str) -> None:
        if self.state != PODState.QUOTED:
            raise PODContractError("invalid_state")
        if _uuid(actor_id, "actor_id") != _uuid(self.order.seller_id, "seller_id"):
            raise PODContractError("seller_not_owned")
        self._event(PODState.APPROVED, approval_ref)
        self.approved_by = str(actor_id)

    def prepare_handoff(self, actor_id: str, approval_ref: str) -> Mapping[str, object]:
        """Prepare, never send, an opaque supplier payload."""
        if self.state != PODState.APPROVED or not self.approved_by:
            raise PODContractError("not_approved")
        if _uuid(actor_id, "actor_id") != _uuid(self.approved_by, "approved_by"):
            raise PODContractError("approval_owner_mismatch")
        if self.events[-1] != (PODState.APPROVED.value, approval_ref):
            raise PODContractError("approval_receipt_mismatch")
        return {
            "order_id": self.order.order_id,
            "supplier_id": self.supplier.supplier_id,
            "variant_id": self.quote.variant_id,
            "quantity": self.order.quantity,
            "artwork_ref": self.order.artwork_ref,
            "idempotency_key": self.idempotency_key,
            "external_execution_performed": False,
            "payment_performed": False,
        }

    def record_submission(self, actor_id: str, external_ref: str) -> None:
        """Record a supplied reference; does not authenticate the external provider.

        A future connector MUST independently verify the provider response before
        calling this method. Never expose this method directly as a client API.
        """
        if self.state != PODState.APPROVED or not self.approved_by:
            raise PODContractError("not_approved")
        if _uuid(actor_id, "actor_id") != _uuid(self.approved_by, "approved_by"):
            raise PODContractError("approval_owner_mismatch")
        if not isinstance(external_ref, str) or not external_ref.strip():
            raise PODContractError("submission_evidence_required")
        self._event(PODState.SUBMITTED, external_ref)
        self.submission_reference = external_ref

    def record_receipt(self, actor_id: str, submission_ref: str, receipt_ref: str) -> None:
        if self.state != PODState.SUBMITTED or not self.submission_reference:
            raise PODContractError("not_submitted")
        if _uuid(actor_id, "actor_id") != _uuid(self.approved_by, "approved_by"):
            raise PODContractError("approval_owner_mismatch")
        if submission_ref != self.submission_reference:
            raise PODContractError("submission_receipt_mismatch")
        if not isinstance(receipt_ref, str) or not receipt_ref.strip():
            raise PODContractError("receipt_evidence_required")
        self._event(PODState.ACCEPTED, receipt_ref)
        self.receipt_reference = receipt_ref

    def stop(self, actor_id: str, reason: str) -> None:
        if _uuid(actor_id, "actor_id") != _uuid(self.order.seller_id, "seller_id"):
            raise PODContractError("seller_not_owned")
        if self.state in (PODState.ACCEPTED, PODState.SUBMITTED):
            self._event(PODState.RECOVERY_REQUIRED, reason)
        elif self.state not in (PODState.STOPPED, PODState.RECOVERY_REQUIRED):
            self._event(PODState.STOPPED, reason)
        else:
            raise PODContractError("invalid_state")

    def fail(self, evidence_ref: str) -> None:
        if self.state not in (PODState.SUBMITTED, PODState.APPROVED):
            raise PODContractError("invalid_state")
        self._event(PODState.RECOVERY_REQUIRED, evidence_ref)

    @property
    def safe_to_retry(self) -> bool:
        """Unknown external state always requires reconciliation before retry."""
        return self.state in (PODState.DRAFT, PODState.QUOTED, PODState.APPROVED) and not self.submission_reference
