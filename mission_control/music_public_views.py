"""Public OAP Music first-party listener front door."""
from flask import Blueprint, jsonify, make_response, render_template, request

from . import (
    entertainment_catalogue,
    music_assets,
    music_entitlements,
    music_public_catalogue,
    web_security,
)

bp = Blueprint("oap_music_public", __name__)
_music_asset_store = music_assets.MusicAssetStore()
_music_entitlement_store = music_entitlements.MusicEntitlementStore()


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.get("/music/manifest.webmanifest")
def music_manifest():
    """Dedicated first-party install identity for the public OAP Music app."""

    response = make_response(
        jsonify(
            {
                "name": "OAP Music",
                "short_name": "OAP Music",
                "description": "First-party OAP Music player, creator and radio surface.",
                "id": "/music",
                "start_url": "/music?source=oap-music-app",
                "scope": "/music",
                "display": "standalone",
                "display_override": ["standalone", "minimal-ui"],
                "orientation": "any",
                "background_color": "#080808",
                "theme_color": "#080808",
                "prefer_related_applications": False,
                "categories": ["music", "entertainment"],
                "icons": [
                    {"src": "/assets/oap-os-icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
                    {"src": "/assets/oap-os-icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
                ],
                "shortcuts": [
                    {"name": "Player", "short_name": "Player", "url": "/music#player"},
                    {"name": "Radio", "short_name": "Radio", "url": "/radio"},
                    {"name": "Creator Studio", "short_name": "Create", "url": "/music/studio"},
                ],
            }
        )
    )
    response.headers["Content-Type"] = "application/manifest+json"
    response.headers["Cache-Control"] = "public, max-age=3600"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.get("/music")
def music_home():
    return _no_store(
        make_response(
            render_template(
                "oap_music.html",
                player=entertainment_catalogue.universal_player_contract(),
                listener=music_public_catalogue.listener_contract(),
            )
        )
    )


@bp.get("/music/studio")
@web_security.login_required()
def music_studio():
    return _no_store(make_response(render_template("oap_music_studio.html")))


@bp.get("/radio")
def radio_home():
    return _no_store(make_response(render_template("oap_radio.html")))


@bp.get("/music/api/song-price")
def music_song_price():
    amount = request.args.get("amount_minor", "100")
    try:
        return _no_store(make_response(jsonify(music_entitlements.song_price_intent(amount))))
    except (TypeError, ValueError) as exc:
        return _no_store(
            make_response(
                jsonify(error={"code": "invalid_song_amount", "message": str(exc)}),
                400,
            )
        )


@bp.get("/music/api/catalogue")
def music_catalogue():
    """Search canonical first-party OAP Music metadata only."""
    try:
        return _no_store(
            make_response(
                jsonify(
                    music_public_catalogue.catalogue(
                        query=request.args.get("q", ""),
                        limit=50,
                    )
                )
            )
        )
    except (ValueError, RuntimeError):
        return _no_store(
            make_response(
                jsonify(
                    {
                        "catalogue": "OAP Music",
                        "ownership": "first_party",
                        "items": [],
                        "item_count": 0,
                        "playback_enabled": False,
                        "external_catalogue_dependency": False,
                        "temporarily_unavailable": True,
                    }
                ),
                503,
            )
        )


@bp.get("/music/api/assets/<asset_id>/stream")
def public_music_stream(asset_id: str):
    """Deliver one globally-cleared first-party asset after live fail-closed gates."""
    try:
        gate = _music_entitlement_store.public_gate(
            asset_id=asset_id,
            territory="*",
            channel="OAP Music",
        )
        if gate.get("allowed") is not True:
            return _no_store(
                make_response(
                    jsonify(
                        error={
                            "code": "public_playback_locked",
                            "message": "This track is not cleared for public playback.",
                        }
                    ),
                    403,
                )
            )
        item = _music_asset_store.read_public_candidate(asset_id=asset_id)
        if item is None:
            return _no_store(
                make_response(
                    jsonify(
                        error={
                            "code": "not_found",
                            "message": "Audio asset unavailable.",
                        }
                    ),
                    404,
                )
            )
        owner_identity_id, media, mime_type, digest, original_name = item
        if owner_identity_id != gate.get("owner_identity_id"):
            return _no_store(
                make_response(
                    jsonify(
                        error={
                            "code": "public_playback_locked",
                            "message": "This track is not cleared for public playback.",
                        }
                    ),
                    403,
                )
            )

        total = len(media)
        status = 200
        body = media
        content_range = None
        requested_range = request.headers.get("Range", "").strip()
        if requested_range:
            if not requested_range.startswith("bytes=") or "," in requested_range:
                response = make_response("", 416)
                response.headers["Content-Range"] = f"bytes */{total}"
                return _no_store(response)
            spec = requested_range[6:]
            start_text, separator, end_text = spec.partition("-")
            if not separator:
                response = make_response("", 416)
                response.headers["Content-Range"] = f"bytes */{total}"
                return _no_store(response)
            try:
                if start_text:
                    range_start = int(start_text)
                    range_end = int(end_text) if end_text else total - 1
                else:
                    suffix = int(end_text)
                    if suffix <= 0:
                        raise ValueError("invalid_range")
                    range_start = max(total - suffix, 0)
                    range_end = total - 1
            except ValueError:
                response = make_response("", 416)
                response.headers["Content-Range"] = f"bytes */{total}"
                return _no_store(response)
            if range_start < 0 or range_start >= total or range_end < range_start:
                response = make_response("", 416)
                response.headers["Content-Range"] = f"bytes */{total}"
                return _no_store(response)
            range_end = min(range_end, total - 1)
            body = media[range_start : range_end + 1]
            status = 206
            content_range = f"bytes {range_start}-{range_end}/{total}"

        response = make_response(body, status)
        response.headers["Content-Type"] = mime_type
        response.headers["Content-Length"] = str(len(body))
        response.headers["ETag"] = f'"{digest}"'
        response.headers["Accept-Ranges"] = "bytes"
        safe_name = (
            original_name.replace(chr(34), "")
            .replace(chr(13), "")
            .replace(chr(10), "")
        )
        response.headers["Content-Disposition"] = f'inline; filename="{safe_name}"'
        response.headers["X-OAP-Rights-Decision"] = str(gate.get("rights_decision_hash"))
        response.headers["X-OAP-Entitlement"] = str(gate.get("entitlement_id"))
        if content_range is not None:
            response.headers["Content-Range"] = content_range
        return _no_store(response)
    except (TypeError, ValueError):
        return _no_store(
            make_response(
                jsonify(error={"code": "invalid_request", "message": "Invalid audio asset."}),
                400,
            )
        )
    except music_assets.MusicAssetStopped:
        return _no_store(
            make_response(
                jsonify(error={"code": "music_asset_stopped", "message": "This track is stopped."}),
                410,
            )
        )
    except (
        music_assets.MusicAssetUnavailable,
        music_entitlements.MusicEntitlementUnavailable,
        RuntimeError,
    ):
        return _no_store(
            make_response(
                jsonify(
                    error={
                        "code": "music_unavailable",
                        "message": "OAP Music is temporarily unavailable.",
                    }
                ),
                503,
            )
        )


@bp.get("/music/api/status")
def music_public_status():
    """Public truth-mode contract for the deployed Music front door."""
    return _no_store(
        make_response(
            jsonify(
                {
                    "organ": "OAP Music",
                    "front_door_ready": True,
                    "install_app_contract_ready": True,
                    "install_manifest_url": "/music/manifest.webmanifest",
                    "install_mode": "PWA",
                    "signed_android_package_verified": False,
                    "device_install_verified": False,
                    "first_party_catalogue_ready": True,
                    "first_party_discovery_ready": True,
                    "listener_contract": music_public_catalogue.listener_contract(),
                    "public_catalogue_track_count": 0,
                    "public_playback_enabled": False,
                    "public_radio_streaming_enabled": False,
                    "rights_verified_by_software": False,
                    "human_authority_final": True,
                }
            )
        )
    )
