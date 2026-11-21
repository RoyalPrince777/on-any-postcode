"""Read-only first-party cash counter authority evidence.

Schema below is a proposed, unapplied migration contract. The resolver
cannot create staff rights, register sites, approve money or move cash.
"""
from __future__ import annotations

from . import postgres_db
from .sika_cash_authority_boundary import CashAuthorityUnavailable

SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_sika_cash_sites (
        site_id TEXT PRIMARY KEY,
        status TEXT NOT NULL CHECK (status IN ('PENDING','ACTIVE','SUSPENDED')),
        physical_site_verified BOOLEAN NOT NULL DEFAULT FALSE,
        regulated_cash_authority_proven BOOLEAN NOT NULL DEFAULT FALSE
    )""",
    """CREATE TABLE IF NOT EXISTS oap_sika_cash_staff (
        site_id TEXT NOT NULL REFERENCES oap_sika_cash_sites(site_id),
        operator_id TEXT NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('ACTIVE','REVOKED','SUSPENDED')),
        cash_permission BOOLEAN NOT NULL DEFAULT FALSE,
        PRIMARY KEY (site_id, operator_id)
    )""",
)


def resolve_authority(site_id: str, operator_id: str) -> dict[str, object]:
    """Read current site/staff records from the server's database only.

    Authenticated operator identity must be bound by the calling server route.
    There is deliberately no public route, write interface or auto migration.
    """
    if not site_id or not operator_id:
        raise CashAuthorityUnavailable("cash_authority_identity_required")
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT s.status, s.physical_site_verified,
                          s.regulated_cash_authority_proven,
                          o.status, o.cash_permission
                   FROM oap_sika_cash_sites s
                   JOIN oap_sika_cash_staff o ON o.site_id=s.site_id
                   WHERE s.site_id=%s AND o.operator_id=%s""",
                (site_id, operator_id),
            ).fetchone()
    except Exception as exc:
        raise CashAuthorityUnavailable("cash_authority_records_unavailable") from exc
    if row is None:
        raise CashAuthorityUnavailable("cash_authority_records_missing")
    return {
        "service_point_id": site_id,
        "operator_id": operator_id,
        "staff_authorised": row[3] == "ACTIVE" and row[4] is True,
        "site_verified": row[0] == "ACTIVE" and row[1] is True,
        "regulated_cash_authority_proven": row[2] is True,
    }
