"""Evidence-backed OAP Music Rank projection.

Rank uses first-party qualified engagement and reconciled creator value only.
It does not use raw page views, queued radio rotations, money paid for promotion,
or unproven external metrics.
"""
from __future__ import annotations

from uuid import UUID

from . import postgres_db


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def track_rank(owner_identity_id: object, *, limit: int = 100) -> dict[str, object]:
    owner = _uuid(owner_identity_id, "owner_identity_id")
    effective_limit = min(100, max(1, int(limit)))
    with postgres_db.connect(readonly=True) as connection:
        rows = connection.execute(
            """SELECT
                 t.track_id,
                 t.title,
                 r.release_id,
                 r.title,
                 COUNT(*) FILTER (WHERE e.qualified=TRUE) AS qualified_events,
                 COUNT(DISTINCT e.listener_key) FILTER (WHERE e.qualified=TRUE) AS unique_listeners,
                 COUNT(*) FILTER (WHERE e.surface='OAP_RADIO' AND e.qualified=TRUE) AS radio_plays,
                 COALESCE(SUM(a.gross_amount_minor) FILTER (WHERE a.state='RECONCILED'),0) AS reconciled_value
               FROM oap_music_tracks t
               JOIN oap_music_releases r ON r.release_id=t.release_id
               LEFT JOIN oap_music_content_groups g ON g.track_id=t.track_id
               LEFT JOIN oap_music_engagement_events e ON e.content_group_id=g.content_group_id
               LEFT JOIN oap_music_creator_allocations a
                 ON a.beneficiary_identity_id=r.owner_identity_id
                AND a.state='RECONCILED'
               WHERE r.owner_identity_id=%s
               GROUP BY t.track_id,t.title,r.release_id,r.title
               ORDER BY t.track_id
               LIMIT %s""",
            (owner, effective_limit),
        ).fetchall()

    scored = []
    for row in rows:
        qualified = int(row[4] or 0)
        unique = int(row[5] or 0)
        radio = int(row[6] or 0)
        value = int(row[7] or 0)
        score = qualified + (unique * 2) + radio + min(value // 100, 1000)
        scored.append(
            {
                "track_id": str(row[0]),
                "track_title": str(row[1]),
                "release_id": str(row[2]),
                "release_title": str(row[3]),
                "qualified_events": qualified,
                "unique_listeners": unique,
                "radio_qualified_plays": radio,
                "reconciled_value_minor": value,
                "rank_score": score,
            }
        )
    scored.sort(key=lambda item: (-int(item["rank_score"]), str(item["track_id"])))
    for index, item in enumerate(scored, start=1):
        item["position"] = index

    return {
        "lane": "Track",
        "scope": "owner",
        "method": "qualified_engagement_unique_radio_reconciled_value_v1",
        "items": scored,
        "item_count": len(scored),
        "raw_views_used": False,
        "paid_promotion_used": False,
        "queued_radio_used": False,
        "external_metrics_used": False,
        "human_authority_final": True,
    }
