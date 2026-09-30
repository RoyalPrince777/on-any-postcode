"""Read-only Property authority check in OAP's existing PostgreSQL database.

Evidence issuance, document verification, review and migration are separate gated
work. A reference alone, an ACTIVE flag alone, or merchant certification alone
never confers property advertising rights.
"""
from __future__ import annotations

from uuid import UUID

from . import authority, postgres_db


def verified_advertising_authority(record: dict, evidence_ref: str) -> bool:
    """Require a scoped, independently reviewed, unexpired, non-revoked grant.

    Checks are re-run by the Property lifecycle at approval, publication and
    projection. No network calls or writes; a missing migration denies access.
    """
    try:
        evidence_id = str(UUID(str(evidence_ref)))
        publisher = str(UUID(str(record["publisher_id"])))
        advertiser = str(UUID(str(record["advertiser_id"])))
        property_ref = record["property_ref"]
        country = record["country"]
        if not isinstance(property_ref, str) or not property_ref.strip():
            return False
        if not isinstance(country, str) or not country.strip():
            return False
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT reviewed_by FROM oap_property_advertising_authority
                   WHERE evidence_id=%s AND publisher_id=%s AND advertiser_id=%s
                     AND property_ref=%s AND country=%s AND activity='ADVERTISE'
                     AND status='ACTIVE' AND revoked_at IS NULL
                     AND valid_from<=CURRENT_TIMESTAMP
                     AND valid_until>CURRENT_TIMESTAMP
                     AND reviewed_by<>publisher_id
                     AND reviewed_at IS NOT NULL
                     AND evidence_sha256 ~ '^[0-9a-f]{64}$'
                     AND length(trim(grantor_reference))>0
                   LIMIT 1""",
                (evidence_id, publisher, advertiser, property_ref, country),
            ).fetchone()
            if row is None:
                return False
            # Reviewer must STILL hold canonical active level-zero authority.
            authority.require_human_authority(connection, str(UUID(str(row[0]))))
        return True
    except Exception:  # noqa: BLE001 - invalid/missing/revoked grants deny.
        return False
