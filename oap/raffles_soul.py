"""Raffles SOUL: privacy and release boundary; shared Matrix remains canonical."""
from __future__ import annotations

from dataclasses import dataclass

PROTECTED = frozenset({"identity_document", "date_of_birth", "email", "phone",
                       "payment_details", "home_address", "health", "biometric"})
RELEASE_GATES = ("independent_legal_review", "verified_prize_fulfilment",
                 "canonical_audit_readback", "authenticated_founder_final",
                 "territory_eligibility", "youth_safeguards",
                 "entry_and_winner_integrity")

@dataclass(frozen=True)
class SoulResult:
    scope: str
    missing: tuple[str, ...]
    safe_evidence: dict[str, str]
    release_allowed: bool = False


def review(*, evidence: dict[str, str] | None = None,
           territory: str = "uk") -> SoulResult:
    """Do not equate submitted claims with verified release authority."""
    supplied = evidence if isinstance(evidence, dict) else {}
    safe = {k: str(v)[:256] for k, v in supplied.items()
            if k not in PROTECTED and isinstance(v, str)}
    missing = tuple(key for key in RELEASE_GATES if not safe.get(key))
    return SoulResult(territory, missing, safe)


def can_public_execute(*_args: object, **_kwargs: object) -> bool:
    """Deployment and entry execution are outside this draft PR's scope."""
    return False
