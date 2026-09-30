"""Canonical identity gates for isolated Property advertising.

These read existing OAP certification and Human Authority records. This module
does NOT attest ownership, create an evidence store, or enable Market publishing.
Property authority evidence must be checked separately by an approved provider.
"""
from __future__ import annotations

from uuid import UUID

from . import authority, certification, postgres_db


def certified_merchant(identity_id: str) -> bool:
    """Read active canonical Certified Merchant state; errors deny."""
    try:
        target = str(UUID(str(identity_id)))
        return certification.identity_status(target).get("merchant") is True
    except Exception:  # noqa: BLE001 - no certification fallback on outages.
        return False


def independent_human_reviewer(reviewer_id: str, publisher_id: str) -> bool:
    """Require a distinct active, level-zero Human Authority in the OAP store."""
    try:
        reviewer = str(UUID(str(reviewer_id)))
        publisher = str(UUID(str(publisher_id)))
        if reviewer == publisher:
            return False
        with postgres_db.connect(readonly=True) as connection:
            authority.require_human_authority(connection, reviewer)
        return True
    except Exception:  # noqa: BLE001 - no authority fallback on outages.
        return False
