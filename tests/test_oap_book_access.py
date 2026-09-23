"""Isolated Book Access policy regressions; no DB, payments or deployment."""

from datetime import datetime, timedelta, timezone

import pytest

from mission_control.oap_book_access import Access, Book, Rotation, decide_access

NOW = datetime(2026, 9, 23, tzinfo=timezone.utc)


def book(**changes):
    return Book(book_id="premium-1", premium=True,
                rights_evidence="signed-permission-1", rights_allow_rotation=True,
                **changes)


def rotation():
    return Rotation("premium-1", NOW, NOW + timedelta(days=7))


def test_core_remains_free_before_and_after_rotation():
    core = Book(book_id="food-book", core_free=True)
    assert decide_access(core, user_id=None, now=NOW).access is Access.FREE
    assert decide_access(core, user_id=None, now=NOW + timedelta(days=20)).access is Access.FREE


def test_rotation_begins_inclusively_and_ends_exclusively():
    for instant, expected in (
        (NOW - timedelta(seconds=1), Access.DENIED),
        (NOW, Access.ROTATION),
        (NOW + timedelta(days=7) - timedelta(seconds=1), Access.ROTATION),
        (NOW + timedelta(days=7), Access.DENIED),
    ):
        result = decide_access(book(), user_id="reader", rotation=rotation(), now=instant)
        assert result.access is expected
        if expected is Access.ROTATION:
            assert result.rotation_ends_at == NOW + timedelta(days=7)


def test_purchase_survives_rotation_end():
    result = decide_access(book(), user_id="buyer",
                           purchased_book_ids=frozenset({"premium-1"}),
                           rotation=rotation(), now=NOW + timedelta(days=10))
    assert result.access is Access.PURCHASED


@pytest.mark.parametrize("changed", [
    {"rights_evidence": None},
    {"rights_allow_rotation": False},
    {"private": True},
    {"core_free": True},
    {"premium": False},
    {"youth": True},
])
def test_rotation_fails_closed_without_all_required_evidence(changed):
    base = {"book_id": "premium-1", "premium": True,
            "rights_evidence": "signed-permission-1", "rights_allow_rotation": True}
    base.update(changed)
    result = decide_access(Book(**base), user_id="reader", rotation=rotation(), now=NOW)
    assert result.access is Access.DENIED


def test_youth_rotation_requires_both_checks():
    youth = Book(book_id="premium-1", premium=True, youth=True,
                 rights_evidence="signed", rights_allow_rotation=True,
                 safeguarding_approved=True, age_approved=True)
    assert decide_access(youth, user_id="reader", rotation=rotation(), now=NOW).access is Access.ROTATION


def test_private_owner_only_and_no_preview():
    private = Book(book_id="private-1", private=True, core_free=True)
    for reader in (None, "stranger"):
        assert decide_access(private, user_id=reader, owner_id="owner",
                             preview=True, now=NOW).access is Access.DENIED
    assert decide_access(private, user_id="owner", owner_id="owner",
                         now=NOW).access is Access.PURCHASED


def test_preview_never_grants_full_access():
    assert decide_access(book(), user_id=None, now=NOW, preview=True).access is Access.PREVIEW


def test_invalid_rotation_length_and_naive_clock_fail_closed():
    wrong = Rotation("premium-1", NOW, NOW + timedelta(days=8))
    assert decide_access(book(), user_id="reader", rotation=wrong, now=NOW).access is Access.DENIED
    with pytest.raises(ValueError, match="timezone_required"):
        decide_access(book(), user_id="reader", now=NOW.replace(tzinfo=None))
