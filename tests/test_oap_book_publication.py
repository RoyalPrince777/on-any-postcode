"""Publication evidence must fail closed without inventing publishing rights."""

from datetime import datetime, timedelta, timezone

import pytest

from mission_control.oap_book_publication import EditionEvidence, publication_blocks

NOW = datetime(2026, 9, 23, tzinfo=timezone.utc)


def edition(**changes):
    base = {
        "book_id": "food-advanced",
        "edition_id": "edition-1",
        "manuscript_sha256": "digest",
        "creator_id": "creator",
        "publisher_authority_id": "authority",
        "rights_record_id": "verified-rights",
        "founder_approval_id": "founder-review",
        "rights_verified": True,
        "manuscript_approved": True,
        "public_release_approved": True,
    }
    base.update(changes)
    return EditionEvidence(**base)


def test_verified_approved_edition_has_no_policy_blockers():
    assert publication_blocks(edition(), now=NOW) == ()


@pytest.mark.parametrize("missing", (
    "book_id", "edition_id", "manuscript_sha256", "creator_id",
    "publisher_authority_id", "rights_record_id", "founder_approval_id",
))
def test_missing_evidence_blocks_release(missing):
    assert f"missing_{missing}" in publication_blocks(
        edition(**{missing: ""}), now=NOW
    )


@pytest.mark.parametrize(("changed", "block"), (
    ({"private": True}, "private_edition"),
    ({"rights_verified": False}, "rights_unverified"),
    ({"manuscript_approved": False}, "manuscript_unapproved"),
    ({"public_release_approved": False}, "public_release_unapproved"),
    ({"youth": True}, "youth_checks_missing"),
    ({"expires_at": NOW}, "rights_expired"),
    ({"expires_at": NOW - timedelta(days=1)}, "rights_expired"),
    ({"expires_at": NOW.replace(tzinfo=None)}, "invalid_expiry_timezone"),
))
def test_protected_unverified_or_expired_edition_is_blocked(changed, block):
    assert block in publication_blocks(edition(**changed), now=NOW)


def test_youth_needs_both_checks():
    assert publication_blocks(edition(
        youth=True, safeguarding_approved=True, age_approved=True,
    ), now=NOW) == ()


def test_naive_clock_is_rejected():
    with pytest.raises(ValueError, match="timezone_required"):
        publication_blocks(edition(), now=NOW.replace(tzinfo=None))
