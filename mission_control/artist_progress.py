"""Owner-scoped OAP Music Artist Progress projection.

Progress is evidence-derived from first-party release and accounting records.
No audience, stream, payout, ranking, or distribution metric is fabricated.
"""
from __future__ import annotations

from uuid import UUID

from . import postgres_db


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def artist_progress(identity_id: object) -> dict[str, object]:
    owner = _uuid(identity_id, "identity_id")
    with postgres_db.connect(readonly=True) as connection:
        releases = connection.execute(
            """SELECT r.release_id,r.title,r.release_type,r.state,r.rights_status,
                      r.external_distribution_state,r.created_at,COUNT(t.track_id)
               FROM oap_music_releases r
               LEFT JOIN oap_music_tracks t ON t.release_id=r.release_id
               WHERE r.owner_identity_id=%s
               GROUP BY r.release_id
               ORDER BY r.created_at DESC""",
            (owner,),
        ).fetchall()
        accounting = connection.execute(
            """SELECT
                 COUNT(*) FILTER (WHERE state='PENDING_RECONCILIATION'),
                 COUNT(*) FILTER (WHERE state='RECONCILED'),
                 COUNT(*) FILTER (WHERE state='REVERSED'),
                 COALESCE(SUM(gross_amount_minor) FILTER (
                     WHERE state IN ('PENDING_RECONCILIATION','RECONCILED')
                 ),0),
                 COALESCE(SUM(gross_amount_minor) FILTER (WHERE state='RECONCILED'),0),
                 COALESCE(SUM(gross_amount_minor) FILTER (WHERE state='REVERSED'),0)
               FROM oap_music_creator_allocations
               WHERE beneficiary_identity_id=%s""",
            (owner,),
        ).fetchone()

    release_items = [
        {
            "release_id": str(row[0]),
            "title": str(row[1]),
            "release_type": str(row[2]),
            "state": str(row[3]),
            "rights_status": str(row[4]),
            "distribution_state": str(row[5]),
            "created_at": row[6].isoformat(),
            "track_count": int(row[7]),
        }
        for row in releases
    ]
    state_counts: dict[str, int] = {}
    rights_counts: dict[str, int] = {}
    for release in release_items:
        state = str(release["state"])
        rights = str(release["rights_status"])
        state_counts[state] = state_counts.get(state, 0) + 1
        rights_counts[rights] = rights_counts.get(rights, 0) + 1

    pending = int(accounting[0] or 0) if accounting else 0
    reconciled = int(accounting[1] or 0) if accounting else 0
    reversed_count = int(accounting[2] or 0) if accounting else 0
    gross_active = int(accounting[3] or 0) if accounting else 0
    gross_reconciled = int(accounting[4] or 0) if accounting else 0
    gross_reversed = int(accounting[5] or 0) if accounting else 0

    return {
        "surface": "Artist Progress",
        "owner_identity_id": owner,
        "release_count": len(release_items),
        "track_count": sum(int(item["track_count"]) for item in release_items),
        "release_states": state_counts,
        "rights_states": rights_counts,
        "releases": release_items,
        "accounting": {
            "currency": "GBP",
            "pending_reconciliation_count": pending,
            "reconciled_count": reconciled,
            "reversed_count": reversed_count,
            "gross_active_minor": gross_active,
            "gross_reconciled_minor": gross_reconciled,
            "gross_reversed_minor": gross_reversed,
            "money_transfer_performed": False,
            "sika_execution_performed": False,
        },
        "qualified_listens": None,
        "rank_position": None,
        "radio_spins": None,
        "audience_growth": None,
        "unavailable_metrics_reason": "measurement_core_not_yet_proven",
        "human_authority_final": True,
    }
