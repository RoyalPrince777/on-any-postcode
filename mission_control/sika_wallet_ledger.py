"""First-party SIKA wallet and ledger model for non-settling software state.

This module records owner-scoped SIKA ledger intents and treasury rate
snapshots. It does not create deposits, custody customer funds, or settle money.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from threading import RLock
from uuid import uuid4

from .sika_global import CurrencyError, normalize_currency


@dataclass(frozen=True)
class RateSnapshot:
    currency: str
    gbp_per_unit: str
    source: str
    observed_at: str
    digest: str


@dataclass(frozen=True)
class LedgerEntry:
    entry_id: str
    owner_id: str
    kind: str
    amount_sika: str
    memo: str
    created_at: str
    executable: bool
    digest: str


_LOCK = RLock()
_RATES: dict[str, RateSnapshot] = {}
_ENTRIES: dict[str, list[LedgerEntry]] = {}


def _digest(parts: list[str]) -> str:
    return sha256("|".join(parts).encode("utf-8")).hexdigest()


def set_rate(currency: str, gbp_per_unit: str | int | Decimal, *, source: str) -> RateSnapshot:
    code = normalize_currency(currency)
    value = Decimal(str(gbp_per_unit))
    if value <= 0:
        raise CurrencyError("treasury_rate_must_be_positive")
    clean_source = str(source or "").strip()[:120]
    if not clean_source:
        raise CurrencyError("rate_source_required")
    observed_at = datetime.now(UTC).isoformat()
    digest = _digest([code, str(value), clean_source, observed_at])
    snap = RateSnapshot(code, str(value), clean_source, observed_at, digest)
    with _LOCK:
        _RATES[code] = snap
    return snap


def get_rate(currency: str) -> RateSnapshot | None:
    code = normalize_currency(currency)
    with _LOCK:
        return _RATES.get(code)


def list_rates() -> list[dict[str, str]]:
    with _LOCK:
        return [asdict(_RATES[key]) for key in sorted(_RATES)]


def record_entry(
    owner_id: str,
    kind: str,
    amount_sika: str | int | Decimal,
    *,
    memo: str = "",
) -> LedgerEntry:
    owner = str(owner_id or "").strip()
    if not owner:
        raise ValueError("owner_required")
    category = str(kind or "").strip().lower()
    if category not in {"opening_reference", "credit_reference", "debit_reference"}:
        raise ValueError("unsupported_ledger_entry_kind")
    amount = Decimal(str(amount_sika))
    if amount < 0:
        raise ValueError("amount_must_not_be_negative")
    created_at = datetime.now(UTC).isoformat()
    entry_id = str(uuid4())
    clean_memo = str(memo or "").strip()[:240]
    digest = _digest([
        entry_id, owner, category, str(amount), clean_memo, created_at, "non_executable"
    ])
    item = LedgerEntry(
        entry_id=entry_id,
        owner_id=owner,
        kind=category,
        amount_sika=f"{amount:.2f}",
        memo=clean_memo,
        created_at=created_at,
        executable=False,
        digest=digest,
    )
    with _LOCK:
        _ENTRIES.setdefault(owner, []).append(item)
    return item


def history(owner_id: str) -> list[dict[str, str | bool]]:
    owner = str(owner_id or "").strip()
    with _LOCK:
        return [asdict(item) for item in reversed(_ENTRIES.get(owner, []))]


def balance_reference(owner_id: str) -> Decimal:
    """Return a software reference balance, never a claim on customer funds."""
    total = Decimal(0)
    for item in history(owner_id):
        amount = Decimal(str(item["amount_sika"]))
        if item["kind"] in {"opening_reference", "credit_reference"}:
            total += amount
        elif item["kind"] == "debit_reference":
            total -= amount
    return total
