"""Evidence-backed OAP Music Rank projection.

Owner-scoped performance counts qualified playback sessions once each.
Unattributed creator allocations are deliberately excluded: monetary value must
never be copied onto unrelated tracks. No public chart authority is claimed.
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
                 COUNT(e.playback_session_id) FILTER (WHERE e.qualified=TRUE) AS qualified_sessions,
                 COUNT(DISTINCT e.listener_key) FILTER (WHERE e.qualified=TRUE) AS unique_listeners,
                 COUNT(e.playback_session_id) FILTER (WHERE e.surface='OAP_RADIO' AND e.qualified=TRUE) AS radio_plays
               FROM oap_music_tracks t
               JOIN oap_music_releases r ON r.release_id=t.release_id
               LEFT JOIN oap_music_content_groups g ON g.track_id=t.track_id
               LEFT JOIN oap_music_playback_sessions e ON e.content_group_id=g.content_group_id
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
        score = qualified + (unique * 2) + radio
        scored.append(
            {
                "track_id": str(row[0]),
                "track_title": str(row[1]),
                "release_id": str(row[2]),
                "release_title": str(row[3]),
                "qualified_sessions": qualified,
                "qualified_events": qualified,
                "unique_listeners": unique,
                "radio_qualified_plays": radio,
                "reconciled_value_minor": None,
                "rank_score": score,
            }
        )
    scored.sort(key=lambda item: (-int(item["rank_score"]), str(item["track_id"])))
    for index, item in enumerate(scored, start=1):
        item["position"] = index

    return {
        "lane": "Track",
        "scope": "owner",
        "method": "qualified_sessions_unique_radio_v2",
        "monetary_attribution_used": False,
        "public_chart_authority": False,
        "items": scored,
        "item_count": len(scored),
        "raw_views_used": False,
        "paid_promotion_used": False,
        "queued_radio_used": False,
        "external_metrics_used": False,
        "human_authority_final": True,
    }
