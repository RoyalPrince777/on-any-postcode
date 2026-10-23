"""Standalone OAP PTT front door.

PTT is a top-level OAP communication product. It reuses the existing first-party
voice store, accepted-contact, youth-safety and block guards without being owned
by The Link or Link Up.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, redirect, render_template, request, session

from . import link_relationships, product_store, ptt_guest, web_security

bp = Blueprint("ptt_ui", __name__, template_folder="templates")

PTT_GUEST_ID_KEY = "oap_ptt_guest_id"
PTT_GUEST_CODE_KEY = "oap_ptt_guest_code"


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _accepted_contacts(identity_id: str) -> list[dict[str, str]]:
    try:
        dashboard = product_store.linkup_dashboard(identity_id) or {}
        directory = {
            str(person.get("identity_id")): person
            for person in dashboard.get("directory", [])
        }
        contacts: list[dict[str, str]] = []
        for relation in link_relationships.list_for_identity(identity_id):
            if relation.get("status") != "accepted":
                continue
            peer_id = (
                str(relation["recipient_id"])
                if str(relation["requester_id"]) == identity_id
                else str(relation["requester_id"])
            )
            peer = directory.get(peer_id, {})
            contacts.append(
                {
                    "identity_id": peer_id,
                    "display_name": str(peer.get("display_name") or "OAP Contact"),
                    "card_id": str(
                        peer.get("card_id") or product_store.member_card_id(peer_id)
                    ),
                }
            )
        contacts.sort(key=lambda item: item["display_name"].casefold())
        return contacts
    except (
        product_store.ProductStoreUnavailable,
        link_relationships.LinkRelationshipsUnavailable,
    ):
        return []


def _guest_identity() -> str | None:
    value = session.get(PTT_GUEST_ID_KEY)
    return str(value) if value else None


def _guest_state() -> dict[str, object]:
    identity = _guest_identity()
    if not identity:
        return {"active": False, "identity_id": None, "peer_id": None, "code": None}
    try:
        return ptt_guest.invite_state(identity, session.get(PTT_GUEST_CODE_KEY))
    except (ValueError, ptt_guest.PttGuestUnavailable):
        return {"active": False, "identity_id": identity, "peer_id": None, "code": session.get(PTT_GUEST_CODE_KEY)}


def _mutation_guard(key: str):
    if not web_security.csrf_valid(request):
        return _no_store(make_response(jsonify(error={"code": "csrf_failed"}), 403))
    if not web_security.PUBLIC_WRITE_LIMITER.allow(key):
        return _no_store(make_response(jsonify(error={"code": "rate_limited"}), 429))
    return None


def _pair_error(exc: Exception):
    code = str(exc) or "ptt_pairing_unavailable"
    status = 400 if isinstance(exc, ValueError) else 503
    if code in {"pair_code_already_used", "device_already_paired"}:
        status = 409
    return _no_store(make_response(jsonify(error={"code": code}), status))


@bp.post("/ptt/pair/create")
def create_pair():
    guard = _mutation_guard(f"ptt-pair-create:{request.remote_addr or 'unknown'}")
    if guard:
        return guard
    try:
        invite = ptt_guest.create_invite()
        session[PTT_GUEST_ID_KEY] = invite["identity_id"]
        session[PTT_GUEST_CODE_KEY] = invite["code"]
        if request.is_json:
            return _no_store(make_response(jsonify(invite), 201))
        return redirect("/ptt", code=303)
    except (ValueError, ptt_guest.PttGuestUnavailable) as exc:
        return _pair_error(exc)


@bp.post("/ptt/pair/join")
def join_pair():
    guard = _mutation_guard(f"ptt-pair-join:{request.remote_addr or 'unknown'}")
    if guard:
        return guard
    payload = request.get_json(silent=True) if request.is_json else request.form
    try:
        paired = ptt_guest.join_invite(
            payload.get("code"),
            session.get(PTT_GUEST_ID_KEY),
        )
        session[PTT_GUEST_ID_KEY] = paired["identity_id"]
        session.pop(PTT_GUEST_CODE_KEY, None)
        if request.is_json:
            return _no_store(make_response(jsonify(paired), 200))
        return redirect("/ptt", code=303)
    except (ValueError, ptt_guest.PttGuestUnavailable) as exc:
        return _pair_error(exc)


@bp.get("/ptt/pair/status")
def pair_status():
    return _no_store(make_response(jsonify(_guest_state()), 200))


@bp.post("/ptt/pair/stop")
def stop_pair():
    identity = _guest_identity()
    guard = _mutation_guard(f"ptt-pair-stop:{identity or request.remote_addr or 'unknown'}")
    if guard:
        return guard
    try:
        stopped = bool(identity and ptt_guest.stop(identity))
        session.pop(PTT_GUEST_CODE_KEY, None)
        if request.is_json:
            return _no_store(make_response(jsonify(stopped=stopped), 200))
        return redirect("/ptt", code=303)
    except (ValueError, ptt_guest.PttGuestUnavailable) as exc:
        return _pair_error(exc)


@bp.get("/ptt/contacts")
@web_security.login_required(api=True)
def contacts_api():
    identity_id = web_security.authenticated_identity()
    return _no_store(make_response(jsonify(contacts=_accepted_contacts(identity_id))))


@bp.get("/ptt")
def front_door():
    user = web_security.current_authenticated_user()
    identity_id = str(user["id"]) if user is not None else None
    response = make_response(
        render_template(
            "ptt.html",
            contacts=_accepted_contacts(identity_id) if identity_id else [],
            authenticated=bool(user),
            guest=_guest_state(),
            oap_csrf_token=web_security.csrf_token(),
        )
    )
    return _no_store(response)
