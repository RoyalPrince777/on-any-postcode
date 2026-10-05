"""Fail-closed OAP Book Access policy; no payment or storage side effects.

Integrate this decision boundary into authenticated reading routes only after
owner-scoped entitlement persistence, rights evidence and platform capture
handling have independent release proof.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum


class Access(str, Enum):
    FREE = "free"
    PURCHASED = "purchased"
    ROTATION = "rotation"
    PREVIEW = "preview"
    DENIED = "denied"


@dataclass(frozen=True)
class Book:
    book_id: str
    core_free: bool = False
    premium: bool = False
    private: bool = False
    youth: bool = False
    creator_owned: bool = False
    rights_evidence: str | None = None
    rights_allow_rotation: bool = False
    safeguarding_approved: bool = False
    age_approved: bool = False


@dataclass(frozen=True)
class Rotation:
    book_id: str
    starts_at: datetime
    ends_at: datetime


@dataclass(frozen=True)
class Decision:
    access: Access
    rotation_ends_at: datetime | None = None


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timezone_required")
    return value.astimezone(timezone.utc)


def rotation_valid(book: Book, rotation: Rotation, now: datetime) -> bool:
    start, end, current = map(_utc, (rotation.starts_at, rotation.ends_at, now))
    return (
        book.book_id == rotation.book_id
        and bool(book.book_id and book.rights_evidence and book.rights_allow_rotation)
        and book.premium and not book.private and not book.core_free
        and (not book.youth or (book.safeguarding_approved and book.age_approved))
        and end - start == timedelta(days=7)
        and start <= current < end
    )


def decide_access(
    book: Book,
    *,
    user_id: str | None,
    owner_id: str | None = None,
    purchased_book_ids: frozenset[str] = frozenset(),
    rotation: Rotation | None = None,
    now: datetime,
    preview: bool = False,
) -> Decision:
    """Treat purchases as caller-verified owner-scoped entitlements, never claims.

    Private books are not purchasable/public; owner identity must match before
    reading. This function never accepts a request-supplied ownership assertion.
    """
    _utc(now)
    if not book.book_id:
        return Decision(Access.DENIED)
    if book.private:
        return Decision(Access.PURCHASED if user_id and owner_id == user_id else Access.DENIED)
    if book.core_free:
        return Decision(Access.FREE)
    if user_id and book.book_id in purchased_book_ids:
        return Decision(Access.PURCHASED)
    if rotation is not None and rotation_valid(book, rotation, now):
        return Decision(Access.ROTATION, _utc(rotation.ends_at))
    if preview:
        return Decision(Access.PREVIEW)
    return Decision(Access.DENIED)
