"""Public OAP Eats software surface."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template_string, request

from . import oap_eats, oap_eats_store, web_security

bp = Blueprint("oap_eats", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>OAP Eats</title></head>
<body><main>
<h1>OAP Eats</h1>
<p>Find it. Order it. Bring it.</p>
<nav>
<a href="/eats/status">Status</a>
<a href="/market">OAP Market</a>
<a href="/transport/ride">OAP Rides</a>
</nav>
<p>One World → one shared map → one identity → one movement engine → one SIKA transaction spine.</p>
<small>Software surface only. Live merchant, payment and courier execution stays evidence-gated.</small>
</main></body></html>"""


@bp.get("/eats")
def eats_home():
    return _no_store(make_response(render_template_string(_PAGE), 200))


@bp.get("/eats/status")
def eats_status():
    return _no_store(make_response(jsonify(oap_eats.status()), 200))


@bp.get("/eats/order-states")
def eats_order_states():
    return _no_store(make_response(jsonify({
        "states": [state.value for state in oap_eats.EatsOrderState],
        "human_authority_final": True,
    }), 200))


def _error(code: str, status: int):
    return _no_store(make_response(jsonify(error={"code": code}), status))


@bp.post("/eats/orders")
@web_security.login_required(api=True)
def create_order():
    identity = web_security.authenticated_identity()
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", 403)
    if not web_security.PUBLIC_WRITE_LIMITER.allow(identity):
        return _error("rate_limited", 429)
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return _error("json_object_required", 400)
    try:
        result = oap_eats_store.STORE.create_order(
            customer_identity_id=identity,
            merchant_id=body.get("merchant_id"),
            items=body.get("items"),
            amount_minor=body.get("amount_minor"),
            currency=body.get("currency"),
            fulfilment_mode=body.get("fulfilment_mode"),
            idempotency_key=request.headers.get("Idempotency-Key"),
        )
        return _no_store(make_response(jsonify(result), 201))
    except PermissionError as exc:
        return _error(str(exc) or "eats_access_denied", 403)
    except ValueError as exc:
        code = str(exc) or "invalid_eats_order"
        return _error(code, 409 if code == "idempotency_conflict" else 400)
    except Exception:
        return _error("eats_store_unavailable", 503)


@bp.post("/eats/orders/<order_id>/state")
@web_security.login_required(api=True)
def transition_order(order_id: str):
    identity = web_security.authenticated_identity()
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", 403)
    if not web_security.PUBLIC_WRITE_LIMITER.allow(identity):
        return _error("rate_limited", 429)
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return _error("json_object_required", 400)
    try:
        result = oap_eats_store.STORE.transition(
            order_id=order_id,
            actor_identity_id=identity,
            target_state=body.get("state"),
        )
        return _no_store(make_response(jsonify(result), 200))
    except PermissionError as exc:
        return _error(str(exc) or "eats_access_denied", 403)
    except ValueError as exc:
        return _error(str(exc) or "invalid_eats_transition", 400)
    except Exception:
        return _error("eats_store_unavailable", 503)
