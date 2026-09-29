"""Public read-only projection of canonical first-party OAP Music records.

No external catalogue, player, identity, analytics or media provider is used here.
Metadata publication does not grant playback rights.
"""
from __future__ import annotations

from . import postgres_db

MAX_PUBLIC_ITEMS = 100


def _safe_query(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.strip().split())[:120]


def catalogue(*, query: object = "", limit: int = 50) -> dict[str, object]:
    q = _safe_query(query)
    effective_limit = min(MAX_PUBLIC_ITEMS, max(1, int(limit)))
    params: list[object] = []
    where = [
        "r.state='PUBLISHED'",
        "r.rights_status='VERIFIED'",
    ]
    if q:
        where.append("(LOWER(r.title) LIKE %s OR LOWER(t.title) LIKE %s)")
        needle = f"%{q.casefold()}%"
        params.extend((needle, needle))
    params.append(effective_limit)

    sql = f"""
        SELECT r.release_id,r.title,r.release_type,
               t.track_id,t.title,t.position,t.duration_ms,t.explicit,
               a.asset_id,a.stopped,pe.entitlement_id
        FROM oap_music_releases r
        JOIN oap_music_tracks t ON t.release_id=r.release_id
        LEFT JOIN oap_music_assets a ON a.track_id=t.track_id
        LEFT JOIN LATERAL (
            SELECT e.entitlement_id
            FROM oap_music_entitlements e
            WHERE e.asset_id=a.asset_id
              AND e.access_scope='PUBLIC_FREE'
              AND e.territory='*'
              AND e.channel='OAP Music'
              AND e.active=TRUE
              AND (e.valid_from IS NULL OR e.valid_from <= CURRENT_TIMESTAMP)
              AND (e.valid_until IS NULL OR e.valid_until > CURRENT_TIMESTAMP)
            ORDER BY e.created_at DESC
            LIMIT 1
        ) pe ON TRUE
        WHERE {' AND '.join(where)}
        ORDER BY r.created_at DESC,t.position ASC
        LIMIT %s
    """
    with postgres_db.connect(readonly=True) as connection:
        rows = connection.execute(sql, tuple(params)).fetchall()

    items = [
        {
            "release_id": str(row[0]),
            "release_title": str(row[1]),
            "release_type": str(row[2]),
            "track_id": str(row[3]),
            "track_title": str(row[4]),
            "track_position": int(row[5]),
            "duration_ms": int(row[6]) if row[6] is not None else None,
            "explicit": bool(row[7]),
            "source": "OAP Music first-party",
            "asset_id": str(row[8]) if row[8] is not None else None,
            "playback_enabled": bool(
                row[8] is not None and row[9] is False and row[10] is not None
            ),
            "stream_url": (
                f"/music/api/assets/{row[8]}/stream"
                if row[8] is not None and row[9] is False and row[10] is not None
                else None
            ),
            "playback_gate_revalidated_on_request": True,
        }
        for row in rows
    ]
    return {
        "catalogue": "OAP Music",
        "ownership": "first_party",
        "query": q,
        "items": items,
        "item_count": len(items),
        "public_metadata_only": True,
        "playback_enabled": any(item["playback_enabled"] for item in items),
        "playable_item_count": sum(1 for item in items if item["playback_enabled"]),
        "external_catalogue_dependency": False,
        "external_player_dependency": False,
        "human_authority_final": True,
    }


def listener_contract() -> dict[str, object]:
    return {
        "platform": "OAP Music",
        "ownership": "first_party",
        "surfaces": (
            "home",
            "search",
            "artists",
            "releases",
            "tracks",
            "playlists",
            "library",
            "queue",
            "radio",
            "records",
            "civilization",
            "universal_player",
        ),
        "canonical_release_store": "oap_music_releases",
        "canonical_track_store": "oap_music_tracks",
        "canonical_playlist_store": "oap_music_playlists",
        "canonical_playlist_item_store": "oap_music_playlist_items",
        "external_catalogue_dependency": False,
        "external_identity_dependency": False,
        "external_player_dependency": False,
        "external_analytics_dependency": False,
        "playback_enabled": False,
        "human_authority_final": True,
    }
