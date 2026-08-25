"""Public, non-operational OAP Movement routes."""

from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template

from . import movement

bp = Blueprint("movement", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.get("/movement")
def movement_home():
    """Render Movement architecture without dispatch or carrier operations."""

    response = make_response(
        render_template(
            "movement.html",
            movement=movement.get_public_movement(),
        )
    )
    return _no_store(response)


@bp.get("/movement/status")
def movement_status():
    """Expose only coarse Movement/eSIM readiness without device identifiers."""

    return _no_store(make_response(jsonify(movement.get_public_movement_status())))
