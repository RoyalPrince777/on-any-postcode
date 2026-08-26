"""Read-safe service projections for OAP Tune, Commerce and Post organs.

Writes remain in :mod:`mission_control.product_cores`. This module provides
owner-scoped projections and one bounded playlist membership write. It does not
stream audio, capture money, pay royalties, fulfil externally or hand parcels
to carriers.
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from . import postgres_db, product_cores


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def tune_dashboard(identity_id: object, *, limit: int = 100) -> dict[str, Any]:
    owner = _uuid(identity_id, "identity_id")
    effective_limit = min(100, max(1, int(limit)))
    with postgres_db.connect(readonly=True) as connection:
        releases = connection.execute(
            """SELECT r.release_id,r.title,r.release_type,r.state,r.rights_status,
                      r.external_distribution_state,r.created_at,COUNT(t.track_id)
               FROM oap_music_releases r
               LEFT JOIN oap_music_tracks t ON t.release_id=r.release_id
               WHERE r.owner_identity_id=%s
               GROUP BY r.release_id
               ORDER BY r.created_at DESC LIMIT %s""",
            (owner, effective_limit),
        ).fetchall()
        playlists = connection.execute(
            """SELECT p.playlist_id,p.title,p.visibility,p.created_at,
                      COUNT(i.track_id)
               FROM oap_music_playlists p
               LEFT JOIN oap_music_playlist_items i ON i.playlist_id=p.playlist_id
               WHERE p.owner_identity_id=%s
               GROUP BY p.playlist_id
               ORDER BY p.created_at DESC LIMIT %s""",
            (owner, effective_limit),
        ).fetchall()
    return {
        "organ": "OAP Tune Core",
        "releases": [
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
        ],
        "playlists": [
            {
                "playlist_id": str(row[0]),
                "title": str(row[1]),
                "visibility": str(row[2]),
                "created_at": row[3].isoformat(),
                "track_count": int(row[4]),
            }
            for row in playlists
        ],
        "licensed_audio_delivery": False,
        "external_distribution": False,
        "royalty_payout": False,
        "human_authority_final": True,
    }


def add_playlist_track(
    *,
    owner_identity_id: object,
    playlist_id: object,
    track_id: object,
    position: object,
) -> dict[str, Any]:
    owner = _uuid(owner_identity_id, "owner_identity_id")
    playlist = _uuid(playlist_id, "playlist_id")
    track = _uuid(track_id, "track_id")
    try:
        position_value = int(position)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_playlist_position") from exc
    if not 1 <= position_value <= 10_000:
        raise ValueError("invalid_playlist_position")

    with postgres_db.connect() as connection:
        owned = connection.execute(
            """SELECT 1 FROM oap_music_playlists
               WHERE playlist_id=%s AND owner_identity_id=%s FOR UPDATE""",
            (playlist, owner),
        ).fetchone()
        if owned is None:
            raise PermissionError("playlist_not_owned")
        visible_track = connection.execute(
            """SELECT 1
               FROM oap_music_tracks t
               JOIN oap_music_releases r ON r.release_id=t.release_id
               WHERE t.track_id=%s
                 AND (r.owner_identity_id=%s OR r.state='PUBLISHED')""",
            (track, owner),
        ).fetchone()
        if visible_track is None:
            raise PermissionError("track_not_available")
        existing_position = connection.execute(
            """SELECT track_id FROM oap_music_playlist_items
               WHERE playlist_id=%s AND position=%s""",
            (playlist, position_value),
        ).fetchone()
        if existing_position is not None and str(existing_position[0]) != track:
            raise ValueError("playlist_position_in_use")
        connection.execute(
            """INSERT INTO oap_music_playlist_items(playlist_id,track_id,position)
               VALUES (%s,%s,%s)
               ON CONFLICT (playlist_id,track_id) DO UPDATE SET
                 position=EXCLUDED.position,added_at=CURRENT_TIMESTAMP""",
            (playlist, track, position_value),
        )
        connection.execute(
            "UPDATE oap_music_playlists SET updated_at=CURRENT_TIMESTAMP WHERE playlist_id=%s",
            (playlist,),
        )
        connection.commit()
    return {
        "playlist_id": playlist,
        "track_id": track,
        "position": position_value,
        "audio_delivery_performed": False,
        "consequential_action": False,
    }


def commerce_dashboard(identity_id: object, *, limit: int = 100) -> dict[str, Any]:
    identity = _uuid(identity_id, "identity_id")
    effective_limit = min(100, max(1, int(limit)))
    with postgres_db.connect(readonly=True) as connection:
        storefront = connection.execute(
            """SELECT storefront_id,store_name,slug,state,created_at,updated_at
               FROM oap_commerce_storefronts WHERE seller_identity_id=%s""",
            (identity,),
        ).fetchone()
        products = connection.execute(
            """SELECT id,name,description,price_minor,currency,active,created_at
               FROM products WHERE seller_id=%s
               ORDER BY created_at DESC LIMIT %s""",
            (identity, effective_limit),
        ).fetchall()
        orders = connection.execute(
            """SELECT order_id,buyer_identity_id,seller_identity_id,state,currency,
                      subtotal_minor,created_at
               FROM oap_commerce_orders
               WHERE buyer_identity_id=%s OR seller_identity_id=%s
               ORDER BY created_at DESC LIMIT %s""",
            (identity, identity, effective_limit),
        ).fetchall()
    storefront_view = None
    if storefront is not None:
        storefront_view = {
            "storefront_id": str(storefront[0]),
            "store_name": str(storefront[1]),
            "slug": str(storefront[2]),
            "state": str(storefront[3]),
            "created_at": storefront[4].isoformat(),
            "updated_at": storefront[5].isoformat(),
        }
    return {
        "organ": "OAP Commerce Core",
        "storefront": storefront_view,
        "products": [
            {
                "product_id": str(row[0]),
                "name": str(row[1]),
                "description": str(row[2] or ""),
                "price_minor": int(row[3]),
                "currency": str(row[4]),
                "active": bool(row[5]),
                "created_at": row[6].isoformat(),
            }
            for row in products
        ],
        "orders": [
            {
                "order_id": str(row[0]),
                "role": "buyer" if str(row[1]) == identity else "seller",
                "state": str(row[3]),
                "currency": str(row[4]),
                "subtotal_minor": int(row[5]),
                "created_at": row[6].isoformat(),
            }
            for row in orders
        ],
        "payment_capture": False,
        "money_transfer": False,
        "external_fulfilment": False,
        "human_authority_final": True,
    }


def post_dashboard(identity_id: object, *, limit: int = 100) -> dict[str, Any]:
    identity = _uuid(identity_id, "identity_id")
    effective_limit = min(100, max(1, int(limit)))
    with postgres_db.connect(readonly=True) as connection:
        hubs = connection.execute(
            """SELECT post_office_id,code,name,postcode,borough,country,state
               FROM oap_post_offices ORDER BY country,name LIMIT %s""",
            (effective_limit,),
        ).fetchall()
        requests = connection.execute(
            """SELECT request_id,post_office_id,service_type,state,created_at
               FROM oap_post_office_requests
               WHERE identity_id=%s ORDER BY created_at DESC LIMIT %s""",
            (identity, effective_limit),
        ).fetchall()
        parcels = connection.execute(
            """SELECT parcel_id,post_office_id,direction,state,oap_tracking_code,created_at
               FROM oap_post_office_parcels
               WHERE owner_identity_id=%s ORDER BY created_at DESC LIMIT %s""",
            (identity, effective_limit),
        ).fetchall()
    return {
        "organ": "OAP Post Core",
        "post_offices": [
            {
                "post_office_id": str(row[0]),
                "code": str(row[1]),
                "name": str(row[2]),
                "postcode": str(row[3]) if row[3] else None,
                "borough": str(row[4]) if row[4] else None,
                "country": str(row[5]),
                "state": str(row[6]),
            }
            for row in hubs
        ],
        "requests": [
            {
                "request_id": str(row[0]),
                "post_office_id": str(row[1]) if row[1] else None,
                "service_type": str(row[2]),
                "state": str(row[3]),
                "created_at": row[4].isoformat(),
            }
            for row in requests
        ],
        "parcels": [
            {
                "parcel_id": str(row[0]),
                "post_office_id": str(row[1]) if row[1] else None,
                "direction": str(row[2]),
                "state": str(row[3]),
                "oap_tracking_code": str(row[4]),
                "created_at": row[5].isoformat(),
            }
            for row in parcels
        ],
        "carrier_handoff": False,
        "physical_site_activation": False,
        "public_precise_tracking": False,
        "human_authority_final": True,
    }


def organ_status(identity_id: object) -> dict[str, Any]:
    """Return all three first-party digital organ projections."""
    return {
        "platform": product_cores.platform_status(),
        "tune": tune_dashboard(identity_id),
        "commerce": commerce_dashboard(identity_id),
        "post": post_dashboard(identity_id),
        "consequential_action": False,
    }
