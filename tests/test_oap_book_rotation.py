"""Weekly rotation planner regressions with zero external side effects."""

from datetime import datetime, timedelta, timezone

import pytest

from mission_control.oap_book_access import Book
from mission_control.oap_book_rotation import select_weekly_rotation

MONDAY = datetime(2026, 9, 21, tzinfo=timezone.utc)


def eligible(book_id, **overrides):
    values = {"book_id": book_id, "premium": True,
              "rights_evidence": "signed-grant", "rights_allow_rotation": True}
    values.update(overrides)
    return Book(**values)


def test_exactly_one_seven_day_rotation_selected_deterministically():
    books = [eligible("z"), eligible("a")]
    result = select_weekly_rotation(books, starts_at=MONDAY)
    assert result is not None
    assert result.book_id == "a"
    assert result.starts_at == MONDAY
    assert result.ends_at == MONDAY + timedelta(days=7)


def test_previous_title_not_selected_when_another_eligible():
    result = select_weekly_rotation(
        [eligible("a"), eligible("b")], starts_at=MONDAY, previous_book_id="a"
    )
    assert result is not None
    assert result.book_id == "b"


def test_unlicensed_private_and_unapproved_youth_never_rotate():
    books = [
        eligible("no-grant", rights_allow_rotation=False),
        eligible("private", private=True),
        eligible("youth", youth=True),
        eligible("missing-evidence", rights_evidence=None),
        eligible("free-core", core_free=True),
    ]
    assert select_weekly_rotation(books, starts_at=MONDAY) is None


def test_approved_youth_is_eligible():
    result = select_weekly_rotation(
        [eligible("youth", youth=True, safeguarding_approved=True,
                  age_approved=True)], starts_at=MONDAY
    )
    assert result is not None
    assert result.book_id == "youth"


def test_duplicate_id_fails_closed():
    with pytest.raises(ValueError, match="duplicate_book_id"):
        select_weekly_rotation([eligible("a"), eligible("a")], starts_at=MONDAY)


def test_only_utc_monday_midnight_allowed():
    for invalid in (
        MONDAY.replace(tzinfo=None),
        MONDAY + timedelta(hours=1),
        MONDAY + timedelta(days=1),
    ):
        with pytest.raises(ValueError):
            select_weekly_rotation([eligible("a")], starts_at=invalid)
