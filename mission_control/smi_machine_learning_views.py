"""Founder-private routes for the existing SMI machine-learning engine."""

from flask import Blueprint, jsonify, make_response, request

from . import smi_machine_learning_runtime as runtime
from . import web_security

bp = Blueprint("smi_machine_learning", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.get("/ml/status")
@web_security.login_required(api=True, founder_only=True)
def machine_learning_status():
    return _no_store(make_response(jsonify(runtime.status())))


@bp.get("/ml/verify")
@web_security.login_required(api=True, founder_only=True)
def machine_learning_verify():
    result = runtime.synthetic_acceptance()
    return _no_store(make_response(jsonify(result), 200 if result["passed"] else 503))


@bp.post("/ml/evaluate")
@web_security.login_required(api=True, founder_only=True)
def machine_learning_evaluate():
    if not web_security.csrf_valid(request):
        return _no_store(make_response(jsonify(error="csrf_failed"), 403))
    try:
        result = runtime.evaluate(request.get_json(silent=True))
    except (TypeError, ValueError) as exc:
        return _no_store(make_response(jsonify(error=str(exc)), 400))
    return _no_store(make_response(jsonify(result)))
