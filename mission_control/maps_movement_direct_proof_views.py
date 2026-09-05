"""Founder-only read-only routes for Maps + Movement + Direct proof runner."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response

from . import maps_movement_direct_proof_runner, web_security

bp = Blueprint("maps_movement_direct_proof", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.get("/proof-runner/maps-movement-direct")
@bp.get("/maps-movement-direct/proof-runner")
@bp.get("/movement-direct-map/proof-runner")
@web_security.login_required(api=True)
def maps_movement_direct_proof_status():
    """Return the current read-only proof-runner projection."""

    return _no_store(
        make_response(jsonify(maps_movement_direct_proof_runner.status()))
    )


@bp.get("/war-room/actions/maps-movement-direct-proof")
@bp.get("/war-room/actions/green-gate/maps-movement-direct")
@web_security.login_required(api=True)
def maps_movement_direct_green_gate_projection():
    """Project proof runner state into the War Room / Green Gate language."""

    proof = maps_movement_direct_proof_runner.status()
    summary = dict(proof.get("summary") or {})
    building = int(summary.get("building") or 0)
    state = "building" if building else "certified"
    signal = "yellow" if building else "green"
    return _no_store(
        make_response(
            jsonify(
                action_id="maps-movement-direct-proof",
                label="Maps + Movement + Direct Proof",
                state=state,
                signal=signal,
                message=(
                    "Proof runner is wired into Green Gate. Unproven route, supplier, "
                    "inventory, photo, HRM and reservation lifecycle checks stay Building."
                ),
                can_execute=False,
                can_approve=False,
                no_fake_green=True,
                green_gate={
                    "reads_proof_runner": True,
                    "state_truthful": True,
                    "execution_granted": False,
                    "payment_capture_enabled": False,
                    "dispatch_enabled": False,
                    "confirmed_reservation_claim_enabled": False,
                },
                proof_runner=proof,
            )
        )
    )
