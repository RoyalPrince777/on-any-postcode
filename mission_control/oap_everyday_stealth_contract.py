"""Isolated, in-memory OAP EVERYDAY stealth creative intake contract.

Not wired to routes, databases, payment processors or public publishing.
No customer PII is accepted or persisted by this module.
"""
from dataclasses import dataclass
from enum import Enum

PACKAGES = {
    "free": (0, 1, 0),
    "quick": (25, 1, 1),
    "starter": (75, 1, 2),
    "plus": (150, 3, 2),
}
FREE_CAPACITY = 10


class State(str, Enum):
    REQUESTED = "requested"
    BRIEF_APPROVED = "brief_approved"
    RIGHTS_APPROVED = "rights_approved"
    PAYMENT_CONFIRMED = "payment_confirmed"
    DELIVERED = "delivered"
    STOPPED = "stopped"


@dataclass(frozen=True)
class Order:
    reference: str
    package: str
    state: State = State.REQUESTED
    rights_evidence: bool = False
    payment_evidence: bool = False


class StealthCreative:
    """Review-only contract; never charges, publishes, uploads or sends."""

    def __init__(self):
        self.orders = {}
        self.stopped = False

    def request(self, reference: str, package: str) -> Order:
        if self.stopped:
            raise PermissionError("STOP")
        if not reference or not reference.isascii() or not reference.replace("-", "").isalnum():
            raise ValueError("Opaque alphanumeric reference required")
        if package not in PACKAGES:
            raise ValueError("Unknown package")
        if reference in self.orders:
            existing = self.orders[reference]
            if existing.package != package:
                raise ValueError("Reference collision")
            return existing
        if package == "free" and sum(o.package == "free" for o in self.orders.values()) >= FREE_CAPACITY:
            raise ValueError("Free capacity exhausted")
        order = Order(reference, package)
        self.orders[reference] = order
        return order

    def advance(self, reference: str, *, founder: bool, rights: bool = False,
                payment: bool = False) -> Order:
        if self.stopped:
            raise PermissionError("STOP")
        if not founder:
            raise PermissionError("Founder approval required")
        order = self.orders[reference]
        if order.state in (State.STOPPED, State.DELIVERED):
            raise ValueError("Terminal order")
        if order.state == State.REQUESTED:
            new = Order(reference, order.package, State.BRIEF_APPROVED)
        elif order.state == State.BRIEF_APPROVED:
            if not rights:
                raise PermissionError("Rights evidence required")
            new = Order(reference, order.package, State.RIGHTS_APPROVED, True)
        elif order.state == State.RIGHTS_APPROVED:
            if order.package == "free":
                new = Order(reference, order.package, State.PAYMENT_CONFIRMED, True, False)
            else:
                if not payment:
                    raise PermissionError("Independent payment evidence required")
                new = Order(reference, order.package, State.PAYMENT_CONFIRMED, True, True)
        else:
            new = Order(reference, order.package, State.DELIVERED,
                        order.rights_evidence, order.payment_evidence)
        self.orders[reference] = new
        return new

    def stop(self, *, founder: bool):
        if not founder:
            raise PermissionError("Founder approval required")
        self.stopped = True

    def recover(self, *, founder: bool, independent_evidence: bool):
        if not founder or not independent_evidence:
            raise PermissionError("Founder and independent recovery evidence required")
        self.stopped = False
