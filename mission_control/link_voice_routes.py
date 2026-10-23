"""Authenticated first-party OAP Link Voice and Share routes."""
from __future__ import annotations

from urllib.parse import quote

from flask import Blueprint, jsonify, make_response, request, session

from . import link_share, link_voice, ptt_guest, web_security

bp = Blueprint("link_voice", __name__)

VOICE_ERRORS = (TypeError, ValueError, link_voice.LinkVoiceUnavailable)
SHARE_ERRORS = (TypeError, ValueError, link_share.LinkShareUnavailable)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _error(code: str, status_code: int):
    return _no_store(make_response(jsonify(error={"code": code}), status_code))


def _identity() -> str:
    return web_security.authenticated_identity()


def _guest_identity() -> str:
    value = session.get("oap_ptt_guest_id")
    if not value:
        raise ValueError("ptt_pair_required")
    return str(value)


def _guest_pair() -> tuple[str, dict[str, object]]:
    identity = _guest_identity()
    try:
        pair = ptt_guest.active_pair(identity)
    except ptt_guest.PttGuestUnavailable as exc:
        raise link_voice.LinkVoiceUnavailable("ptt_pairing_unavailable") from exc
    if pair is None:
        raise ValueError("ptt_pair_required")
    return identity, pair


def _mutation_guard(identity: str):
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", 403)
    if not web_security.PUBLIC_WRITE_LIMITER.allow(identity):
        return _error("rate_limited", 429)
    return None


def _failure(exc: TypeError | ValueError | link_voice.LinkVoiceUnavailable):
    code = str(exc) or "voice_unavailable"
    if isinstance(exc, (TypeError, ValueError)):
        if code in {"link_blocked", "accepted_link_required"}:
            return _error(code, 403)
        if code == "voice_too_large":
            return _error(code, 413)
        return _error(code, 400)
    return _error("voice_unavailable", 503)


def _share_failure(exc: TypeError | ValueError | link_share.LinkShareUnavailable):
    code = str(exc) or "share_unavailable"
    if isinstance(exc, (TypeError, ValueError)):
        if code in {"link_blocked", "accepted_link_required"}:
            return _error(code, 403)
        if code == "share_too_large":
            return _error(code, 413)
        return _error(code, 400)
    return _error("share_unavailable", 503)


@bp.get("/linkup/voice/status")
@web_security.login_required(api=True)
def status():
    state = link_voice.status()
    return _no_store(
        make_response(
            jsonify(
                ready=bool(state.get("ready")),
                first_party=bool(state.get("first_party")),
                max_voice_bytes=state.get("max_voice_bytes"),
                max_voice_duration_ms=state.get("max_voice_duration_ms"),
                ptt_supported=True,
            )
        )
    )


@bp.get("/linkup/voice")
@web_security.login_required(api=True)
def list_voice():
    peer_id = request.args.get("peer_id", "")
    try:
        notes = link_voice.list_voice(_identity(), peer_id)
        return _no_store(make_response(jsonify(voices=notes)))
    except VOICE_ERRORS as exc:
        return _failure(exc)


def _create_voice_kind(kind: str):
    identity = _identity()
    if guarded := _mutation_guard(identity):
        return guarded
    try:
        upload = request.files.get("voice")
        if upload is None:
            raise ValueError("voice_required")
        media = upload.stream.read(link_voice.MAX_VOICE_BYTES + 1)
        if len(media) > link_voice.MAX_VOICE_BYTES:
            raise ValueError("voice_too_large")
        created = link_voice.create_voice(
            identity,
            request.form.get("recipient_id"),
            media=media,
            mime_type=upload.mimetype,
            duration_ms=request.form.get("duration_ms"),
            kind=kind,
        )
        return _no_store(make_response(jsonify(created), 201))
    except VOICE_ERRORS as exc:
        return _failure(exc)


@bp.post("/linkup/voice")
@web_security.login_required(api=True)
def create_voice():
    return _create_voice_kind("voice")


@bp.get("/linkup/ptt/status")
@web_security.login_required(api=True)
def linkup_ptt_status():
    state = link_voice.status()
    return _no_store(
        make_response(
            jsonify(
                ready=bool(state.get("ptt_ready")),
                first_party=bool(state.get("first_party")),
                transport="oap_voice_store",
                push_to_talk=True,
                max_ptt_bytes=state.get("max_voice_bytes"),
                max_ptt_duration_ms=state.get("max_voice_duration_ms"),
            )
        )
    )


@bp.get("/ptt/status")
def guest_ptt_status():
    state = link_voice.status()
    identity = session.get("oap_ptt_guest_id")
    pair = None
    if identity:
        try:
            pair = ptt_guest.active_pair(identity)
        except (ValueError, ptt_guest.PttGuestUnavailable):
            pair = None
    return _no_store(
        make_response(
            jsonify(
                ready=bool(state.get("ptt_ready") and pair),
                transport_ready=bool(state.get("ptt_ready")),
                paired=bool(pair),
                peer_id=pair.get("peer_id") if pair else None,
                first_party=bool(state.get("first_party")),
                transport="oap_voice_store",
                push_to_talk=True,
                max_ptt_bytes=state.get("max_voice_bytes"),
                max_ptt_duration_ms=state.get("max_voice_duration_ms"),
            )
        )
    )


@bp.post("/linkup/ptt")
@web_security.login_required(api=True)
def create_linkup_ptt():
    if not link_voice.status().get("ptt_ready"):
        return _error("ptt_unavailable", 503)
    return _create_voice_kind("ptt")


@bp.post("/ptt")
def create_guest_ptt():
    if not link_voice.status().get("ptt_ready"):
        return _error("ptt_unavailable", 503)
    try:
        identity, pair = _guest_pair()
        if guarded := _mutation_guard(identity):
            return guarded
        upload = request.files.get("voice")
        if upload is None:
            raise ValueError("voice_required")
        media = upload.stream.read(link_voice.MAX_VOICE_BYTES + 1)
        if len(media) > link_voice.MAX_VOICE_BYTES:
            raise ValueError("voice_too_large")
        created = link_voice.create_voice(
            identity,
            pair["peer_id"],
            media=media,
            mime_type=upload.mimetype,
            duration_ms=request.form.get("duration_ms"),
            kind="ptt",
        )
        return _no_store(make_response(jsonify(created), 201))
    except VOICE_ERRORS as exc:
        return _failure(exc)


@bp.get("/ptt/voice")
def list_guest_ptt():
    try:
        identity, pair = _guest_pair()
        notes = [
            note for note in link_voice.list_voice(identity, pair["peer_id"])
            if note.get("kind") == "ptt"
        ]
        return _no_store(make_response(jsonify(voices=notes), 200))
    except VOICE_ERRORS as exc:
        return _failure(exc)


@bp.get("/ptt/voice/<voice_id>/media")
def guest_ptt_media(voice_id: str):
    try:
        identity, pair = _guest_pair()
        result = link_voice.read_voice(identity, pair["peer_id"], voice_id)
        if result is None:
            return _error("voice_not_found", 404)
        media, mime_type, digest = result
        response = make_response(media)
        response.headers["Content-Type"] = mime_type
        response.headers["Content-Length"] = str(len(media))
        response.headers["X-OAP-Content-SHA256"] = digest
        response.headers["Content-Disposition"] = 'inline; filename="ptt"'
        return _no_store(response)
    except VOICE_ERRORS as exc:
        return _failure(exc)


@bp.delete("/ptt/voice/<voice_id>")
def delete_guest_ptt(voice_id: str):
    try:
        identity, _pair = _guest_pair()
        if guarded := _mutation_guard(identity):
            return guarded
        deleted = link_voice.delete_voice(identity, voice_id)
        if not deleted:
            return _error("voice_not_found", 404)
        return _no_store(make_response(jsonify(deleted=True), 200))
    except VOICE_ERRORS as exc:
        return _failure(exc)


def _guest_room() -> tuple[str, dict[str, object]]:
    identity = session.get("oap_ptt_room_identity_id")
    owner = session.get("oap_ptt_room_owner_id")
    if not identity or not owner:
        raise ValueError("ptt_room_required")
    try:
        state = ptt_guest.room_state(identity, owner)
    except ptt_guest.PttGuestUnavailable as exc:
        raise link_voice.LinkVoiceUnavailable("ptt_room_unavailable") from exc
    if not state.get("active"):
        raise ValueError("ptt_room_required")
    return str(identity), state


@bp.post("/ptt/room")
def create_room_ptt():
    if not link_voice.status().get("ptt_ready"):
        return _error("ptt_unavailable", 503)
    try:
        identity, room = _guest_room()
        if guarded := _mutation_guard(identity):
            return guarded
        upload = request.files.get("voice")
        if upload is None:
            raise ValueError("voice_required")
        media = upload.stream.read(link_voice.MAX_VOICE_BYTES + 1)
        if len(media) > link_voice.MAX_VOICE_BYTES:
            raise ValueError("voice_too_large")
        peers = [
            str(peer)
            for peer in room.get("member_ids", [])
            if str(peer) != identity
        ]
        if not peers:
            raise ValueError("ptt_room_no_other_members")
        delivered = []
        for peer in peers:
            delivered.append(
                link_voice.create_voice(
                    identity,
                    peer,
                    media=media,
                    mime_type=upload.mimetype,
                    duration_ms=request.form.get("duration_ms"),
                    kind="ptt",
                )
            )
        return _no_store(
            make_response(
                jsonify(
                    delivered=len(delivered),
                    room_member_count=room.get("member_count"),
                    receipts=delivered,
                ),
                201,
            )
        )
    except VOICE_ERRORS as exc:
        return _failure(exc)


@bp.get("/ptt/room/voice")
def list_room_ptt():
    try:
        identity, room = _guest_room()
        peers = [
            str(peer)
            for peer in room.get("member_ids", [])
            if str(peer) != identity
        ]
        voices = []
        for index, peer in enumerate(peers):
            for note in link_voice.list_voice(identity, peer):
                if note.get("kind") != "ptt":
                    continue
                if note.get("direction") == "sent" and index > 0:
                    continue
                item = dict(note)
                item["peer_id"] = peer
                voices.append(item)
        voices.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
        return _no_store(make_response(jsonify(voices=voices[:100]), 200))
    except VOICE_ERRORS as exc:
        return _failure(exc)


@bp.get("/ptt/room/voice/<voice_id>/media")
def room_ptt_media(voice_id: str):
    try:
        identity, room = _guest_room()
        peer_id = str(request.args.get("peer_id") or "")
        allowed_peers = {
            str(peer)
            for peer in room.get("member_ids", [])
            if str(peer) != identity
        }
        if peer_id not in allowed_peers:
            raise ValueError("ptt_room_peer_required")
        result = link_voice.read_voice(identity, peer_id, voice_id)
        if result is None:
            return _error("voice_not_found", 404)
        media, mime_type, digest = result
        response = make_response(media)
        response.headers["Content-Type"] = mime_type
        response.headers["Content-Length"] = str(len(media))
        response.headers["X-OAP-Content-SHA256"] = digest
        response.headers["Content-Disposition"] = 'inline; filename="ptt-room"'
        return _no_store(response)
    except VOICE_ERRORS as exc:
        return _failure(exc)


@bp.get("/linkup/voice/<voice_id>/media")
@web_security.login_required(api=True)
def voice_media(voice_id: str):
    peer_id = request.args.get("peer_id", "")
    try:
        result = link_voice.read_voice(_identity(), peer_id, voice_id)
        if result is None:
            return _error("voice_not_found", 404)
        media, mime_type, digest = result
        response = make_response(media)
        response.headers["Content-Type"] = mime_type
        response.headers["Content-Length"] = str(len(media))
        response.headers["X-OAP-Content-SHA256"] = digest
        response.headers["Content-Disposition"] = 'inline; filename="voice"'
        return _no_store(response)
    except VOICE_ERRORS as exc:
        return _failure(exc)


@bp.delete("/linkup/voice/<voice_id>")
@web_security.login_required(api=True)
def delete_voice(voice_id: str):
    identity = _identity()
    if guarded := _mutation_guard(identity):
        return guarded
    try:
        deleted = link_voice.delete_voice(identity, voice_id)
        if not deleted:
            return _error("voice_not_found", 404)
        return _no_store(make_response(jsonify(deleted=True)))
    except VOICE_ERRORS as exc:
        return _failure(exc)


@bp.get("/linkup/share/status")
@web_security.login_required(api=True)
def share_status():
    state = link_share.status()
    return _no_store(
        make_response(
            jsonify(
                ready=bool(state.get("ready")),
                first_party=bool(state.get("first_party")),
                max_share_bytes=state.get("max_share_bytes"),
                allowed_mime_types=state.get("allowed_mime_types", []),
            )
        )
    )


@bp.get("/linkup/share")
@web_security.login_required(api=True)
def list_share():
    peer_id = request.args.get("peer_id", "")
    try:
        shares = link_share.list_shares(_identity(), peer_id)
        return _no_store(make_response(jsonify(shares=shares)))
    except SHARE_ERRORS as exc:
        return _share_failure(exc)


@bp.post("/linkup/share")
@web_security.login_required(api=True)
def create_share():
    identity = _identity()
    if guarded := _mutation_guard(identity):
        return guarded
    try:
        upload = request.files.get("share")
        if upload is None:
            raise ValueError("share_required")
        media = upload.stream.read(link_share.MAX_SHARE_BYTES + 1)
        if len(media) > link_share.MAX_SHARE_BYTES:
            raise ValueError("share_too_large")
        created = link_share.create_share(
            identity,
            request.form.get("recipient_id"),
            media=media,
            mime_type=upload.mimetype,
            original_name=upload.filename,
        )
        return _no_store(make_response(jsonify(created), 201))
    except SHARE_ERRORS as exc:
        return _share_failure(exc)


@bp.get("/linkup/share/<share_id>/media")
@web_security.login_required(api=True)
def share_media(share_id: str):
    peer_id = request.args.get("peer_id", "")
    try:
        result = link_share.read_share(_identity(), peer_id, share_id)
        if result is None:
            return _error("share_not_found", 404)
        media, mime_type, digest, original_name, kind = result
        response = make_response(media)
        response.headers["Content-Type"] = mime_type
        response.headers["Content-Length"] = str(len(media))
        response.headers["X-OAP-Content-SHA256"] = digest
        disposition = "inline" if kind in {"photo", "video"} else "attachment"
        response.headers["Content-Disposition"] = (
            f"{disposition}; filename*=UTF-8''{quote(original_name, safe='')}"
        )
        return _no_store(response)
    except SHARE_ERRORS as exc:
        return _share_failure(exc)


@bp.delete("/linkup/share/<share_id>")
@web_security.login_required(api=True)
def delete_share(share_id: str):
    identity = _identity()
    if guarded := _mutation_guard(identity):
        return guarded
    try:
        deleted = link_share.delete_share(identity, share_id)
        if not deleted:
            return _error("share_not_found", 404)
        return _no_store(make_response(jsonify(deleted=True)))
    except SHARE_ERRORS as exc:
        return _share_failure(exc)
