"""Public OAP Music first-party listener front door."""
from flask import Blueprint, jsonify, make_response, render_template, request

from . import (
    artist_progress,
    entertainment_catalogue,
    music_assets,
    music_content_links,
    music_engagement,
    music_entitlements,
    music_public_catalogue,
    music_purchases,
    public_store,
    web_security,
)

bp = Blueprint("oap_music_public", __name__)
_music_asset_store = music_assets.MusicAssetStore()
_music_entitlement_store = music_entitlements.MusicEntitlementStore()
_music_purchase_store = music_purchases.MusicPurchaseStore()


def _identity(*, sync: bool = False) -> str:
    identity_id = web_security.authenticated_identity()
    if sync:
        user = web_security.current_authenticated_user()
        if user is None:
            raise PermissionError("authentication_required")
        public_store.ensure_authenticated_user(
            str(user["id"]),
            email=str(user["email"]),
            display_name=str(user["name"]),
            email_verified=bool(user.get("email_verified")),
        )
    return identity_id


def _api_error(code: str, message: str, status_code: int):
    return _no_store(
        make_response(jsonify(error={"code": code, "message": message}), status_code)
    )


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
                    {"name": "Music", "short_name": "Music", "url": "/music"},
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


@bp.get("/music/artist-progress")
@web_security.login_required()
def music_artist_progress():
    try:
        progress = artist_progress.artist_progress(_identity())
    except Exception:  # noqa: BLE001 - owner progress fails closed.
        progress = {
            "surface": "Artist Progress",
            "release_count": 0,
            "track_count": 0,
            "release_states": {},
            "rights_states": {},
            "releases": [],
            "accounting": {
                "currency": "GBP",
                "pending_reconciliation_count": 0,
                "reconciled_count": 0,
                "reversed_count": 0,
                "gross_active_minor": 0,
                "gross_reconciled_minor": 0,
                "gross_reversed_minor": 0,
                "money_transfer_performed": False,
                "sika_execution_performed": False,
            },
            "qualified_listens": None,
            "rank_position": None,
            "radio_spins": None,
            "audience_growth": None,
            "unavailable_metrics_reason": "artist_progress_temporarily_unavailable",
            "human_authority_final": True,
        }
    return _no_store(
        make_response(render_template("oap_music_artist_progress.html", progress=progress))
    )


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


@bp.post("/music/api/purchases")
@web_security.login_required(api=True)
def music_create_purchase_intent():
    if not web_security.csrf_valid(request):
        return _api_error("csrf_failed", "The secure session expired. Refresh and try again.", 403)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _api_error("invalid_request", "json_object_required", 400)
    try:
        result = _music_purchase_store.create_intent(
            buyer_identity_id=_identity(sync=True),
            item_type=payload.get("item_type"),
            item_id=payload.get("item_id"),
            edition_type=payload.get("edition_type"),
            amount_minor=payload.get("amount_minor"),
            idempotency_key=payload.get("idempotency_key"),
        )
        return _no_store(make_response(jsonify(result), 201))
    except PermissionError as exc:
        return _api_error("permission_denied", str(exc), 403)
    except (TypeError, ValueError) as exc:
        return _api_error("invalid_request", str(exc), 400)
    except Exception:  # noqa: BLE001 - redact storage/provider details.
        return _api_error("music_purchase_unavailable", "Music purchasing is temporarily unavailable.", 503)


@bp.get("/music/api/my-music")
@web_security.login_required(api=True)
def music_my_music():
    try:
        return _no_store(
            make_response(
                jsonify(_music_purchase_store.owned_items(buyer_identity_id=_identity()))
            )
        )
    except PermissionError as exc:
        return _api_error("permission_denied", str(exc), 403)
    except Exception:  # noqa: BLE001 - fail closed and redact store details.
        return _api_error("my_music_unavailable", "My Music is temporarily unavailable.", 503)


@bp.post("/music/api/tracks/<track_id>/content")
@web_security.login_required(api=True)
def music_save_track_content(track_id: str):
    if not web_security.csrf_valid(request):
        return _api_error("csrf_failed", "The secure session expired. Refresh and try again.", 403)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _api_error("invalid_request", "json_object_required", 400)
    try:
        result = music_content_links.save_track_content(
            owner_identity_id=_identity(),
            track_id=track_id,
            lyrics=payload.get("lyrics"),
            credits=payload.get("credits"),
        )
        return _no_store(make_response(jsonify(result), 201))
    except PermissionError as exc:
        return _api_error("permission_denied", str(exc), 403)
    except (TypeError, ValueError) as exc:
        return _api_error("invalid_request", str(exc), 400)
    except Exception:  # noqa: BLE001 - redact storage details.
        return _api_error("music_content_unavailable", "Track content is temporarily unavailable.", 503)


@bp.post("/music/api/tracks/<track_id>/videos")
@web_security.login_required(api=True)
def music_add_video_link(track_id: str):
    if not web_security.csrf_valid(request):
        return _api_error("csrf_failed", "The secure session expired. Refresh and try again.", 403)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _api_error("invalid_request", "json_object_required", 400)
    try:
        result = music_content_links.add_video_link(
            owner_identity_id=_identity(),
            track_id=track_id,
            video_kind=payload.get("video_kind"),
            oap_tv_path=payload.get("oap_tv_path", "/tv-media"),
        )
        return _no_store(make_response(jsonify(result), 201))
    except PermissionError as exc:
        return _api_error("permission_denied", str(exc), 403)
    except (TypeError, ValueError) as exc:
        return _api_error("invalid_request", str(exc), 400)
    except Exception:  # noqa: BLE001 - redact storage details.
        return _api_error("music_video_link_unavailable", "Video linking is temporarily unavailable.", 503)


@bp.post("/music/api/engagement")
def music_record_engagement():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _api_error("invalid_request", "json_object_required", 400)
    try:
        result = music_engagement.record_event(
            track_id=payload.get("track_id"),
            session_identity=web_security.ensure_session_identity(),
            surface=payload.get("surface", "OAP_MUSIC"),
            event_type=payload.get("event_type"),
            playback_seconds=payload.get("playback_seconds", 0),
            duration_seconds=payload.get("duration_seconds"),
            postcode=payload.get("postcode"),
            borough=payload.get("borough"),
            region=payload.get("region"),
            country=payload.get("country"),
            continent=payload.get("continent"),
        )
        return _no_store(make_response(jsonify(result), 201))
    except (TypeError, ValueError) as exc:
        return _api_error("invalid_request", str(exc), 400)
    except Exception:  # noqa: BLE001 - redact storage details.
        return _api_error("engagement_unavailable", "Engagement measurement is temporarily unavailable.", 503)


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
