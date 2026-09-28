"""Deterministic first-party weekly book rotation selection.

This module plans eligible rotations only. It never publishes books, changes
entitlements or triggers a payment. Store the returned schedule and rights
evidence in an authenticated, audited service before any reader integration.
"""
from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta, timezone

from .oap_book_access import Book, Rotation, rotation_valid


def select_weekly_rotation(
    books: Iterable[Book],
    *,
    starts_at: datetime,
    previous_book_id: str | None = None,
) -> Rotation | None:
    """Select exactly one permitted book for a seven-day UTC interval.

    Eligible books must have rights evidence explicitly permitting rotation;
    protected/private and unapproved youth books are never selected.
    No eligible book means no rotation, rather than invented free access.
    """
    if starts_at.tzinfo is None or starts_at.utcoffset() is None:
        raise ValueError("timezone_required")
    start = starts_at.astimezone(timezone.utc)
    if start != start.replace(hour=0, minute=0, second=0, microsecond=0):
        raise ValueError("utc_midnight_required")
    if start.weekday() != 0:
        raise ValueError("monday_required")
    end = start + timedelta(days=7)
    candidates: dict[str, Book] = {}
    for book in books:
        rotation = Rotation(book.book_id, start, end)
        if rotation_valid(book, rotation, start):
            if book.book_id in candidates:
                raise ValueError("duplicate_book_id")
            candidates[book.book_id] = book
    if not candidates:
        return None
    selected = sorted(candidates)
    if len(selected) > 1 and previous_book_id in selected:
        selected.remove(previous_book_id)
    return Rotation(selected[0], start, end)
