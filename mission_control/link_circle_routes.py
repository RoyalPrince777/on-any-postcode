"""Private OAP Link Circle membership routes."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, redirect, render_template, request, url_for

from . import link_circles, postgres_db, web_security

bp = Blueprint("link_circles", __name__)


def _identity() -> str:
    return web_security.authenticated_identity()


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _error(code: str, status_code: int):
    return _no_store(make_response(jsonify(error={"code": code}), status_code))


def _mutation_guard():
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", 403)
    return None


def _accepted_people(identity: str) -> list[dict[str, str]]:
    """Return only current accepted Links as possible Bring In candidates."""
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT u.id,COALESCE(u.display_name,u.username),COALESCE(u.postcode,'')
                   FROM link_relationships r
                   JOIN users u ON u.id=CASE WHEN r.requester_id=%s THEN r.recipient_id ELSE r.requester_id END
                   WHERE (r.requester_id=%s OR r.recipient_id=%s)
                     AND r.status='accepted'
                     AND (r.link_kind='permanent' OR r.expires_at>CURRENT_TIMESTAMP)
                     AND u.status='active'
                   ORDER BY COALESCE(u.display_name,u.username) LIMIT 100""",
                (identity, identity, identity),
            ).fetchall()
    except Exception as exc:
        raise link_circles.LinkCirclesUnavailable("circle_links_unavailable") from exc
    return [
        {"identity_id": str(row[0]), "display_name": str(row[1]), "postcode": str(row[2] or "")}
        for row in rows
    ]


def _notice(code: str):
    return redirect(url_for(".circle_page", notice=code), code=303)


@bp.get("/linkup/circles/status")
@web_security.login_required(api=True)
def circle_status():
    state = link_circles.status()
    return _no_store(make_response(jsonify(
        ready=bool(state.get("ready")),
        first_party=True,
        max_members=link_circles.MAX_CIRCLE_MEMBERS,
        circle_messages_ready=False,
        circle_calls_ready=False,
    )))


@bp.get("/linkup/circles")
@web_security.login_required()
def circle_page():
    identity = _identity()
    state = link_circles.status()
    data = {"circles": [], "invites": [], "max_members": link_circles.MAX_CIRCLE_MEMBERS}
    people: list[dict[str, str]] = []
    unavailable = not bool(state.get("ready"))
    if not unavailable:
        try:
            data = link_circles.dashboard(identity)
            people = _accepted_people(identity)
        except link_circles.LinkCirclesUnavailable:
            unavailable = True
    response = make_response(render_template(
        "link_circles.html",
        circle_data=data,
        accepted_people=people,
        circle_ready=not unavailable,
        notice=str(request.args.get("notice") or "")[:80],
    ))
    return _no_store(response)


@bp.post("/linkup/circles")
@web_security.login_required()
def circle_create():
    guarded = _mutation_guard()
    if guarded is not None:
        return guarded
    try:
        link_circles.create_circle(_identity(), request.form.get("name"))
        return _notice("circle-created")
    except ValueError as exc:
        return _notice(str(exc) or "circle-create-failed")
    except link_circles.LinkCirclesUnavailable:
        return _notice("circle-unavailable")


@bp.post("/linkup/circles/<circle_id>/bring-in")
@web_security.login_required()
def circle_bring_in(circle_id: str):
    guarded = _mutation_guard()
    if guarded is not None:
        return guarded
    try:
        link_circles.bring_in(_identity(), circle_id, request.form.get("invitee_id"))
        return _notice("bring-in-sent")
    except ValueError as exc:
        return _notice(str(exc) or "bring-in-failed")
    except link_circles.LinkCirclesUnavailable:
        return _notice("circle-unavailable")


@bp.post("/linkup/circles/invites/<invite_id>/respond")
@web_security.login_required()
def circle_invite_respond(invite_id: str):
    guarded = _mutation_guard()
    if guarded is not None:
        return guarded
    try:
        if not link_circles.respond_invite(_identity(), invite_id, request.form.get("decision")):
            return _notice("invite-not-found")
        return _notice("linked-in" if request.form.get("decision") == "accepted" else "invite-declined")
    except ValueError as exc:
        return _notice(str(exc) or "link-in-failed")
    except link_circles.LinkCirclesUnavailable:
        return _notice("circle-unavailable")


@bp.post("/linkup/circles/<circle_id>/step-out")
@web_security.login_required()
def circle_step_out(circle_id: str):
    guarded = _mutation_guard()
    if guarded is not None:
        return guarded
    try:
        if not link_circles.step_out(_identity(), circle_id):
            return _notice("circle-not-found")
        return _notice("stepped-out")
    except (ValueError, link_circles.LinkCirclesUnavailable):
        return _notice("circle-unavailable")
