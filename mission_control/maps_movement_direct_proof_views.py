"""Founder-only read-only routes for OAP Atlas + Movement + Direct proof runner."""
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
                action_id="oap-atlas-movement-direct-proof",
                label="OAP Atlas + Movement + Direct Proof",
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


@bp.get("/war-room/actions/a5-atlas-movement-direct")
@bp.get("/war-room/actions/a5-direct-atlas-movement")
@bp.get("/war-room/a5/atlas-movement-direct")
@web_security.login_required(api=True)
def a5_atlas_movement_direct_projection():
    """Expose A5-ready operational capability without unlocking autonomous execution."""

    proof = maps_movement_direct_proof_runner.status()
    return _no_store(
        make_response(
            jsonify(
                action_id="a5-atlas-movement-direct",
                label="A5-ready: OAP Atlas + Movement + OAP Direct",
                state="locked_ready",
                signal="yellow",
                message=(
                    "A5-ready can review, score and prepare command packs for OAP Atlas, "
                    "Movement and OAP Direct. Real A5 autonomy remains locked until separate "
                    "Founder approval, Guardian pass, Green Gate proof and HRM receipts exist."
                ),
                public=False,
                founder_only=True,
                no_fake_green=True,
                autonomy_level="A5-ready locked",
                active_autonomy="A4 supervised",
                can_execute=False,
                can_approve=False,
                can_self_promote=False,
                can_deploy=False,
                can_capture_payment=False,
                can_dispatch=False,
                can_confirm_reservation=False,
                can_track_without_consent=False,
                allowed_capabilities=(
                    "read_route_matrix_contract",
                    "score_21_signals",
                    "review_private_guard_evidence",
                    "review_oap_atlas_source_health",
                    "review_movement_schema_readiness",
                    "review_direct_supplier_listing_inventory_readiness",
                    "review_pictures_lifecycle_receipts",
                    "prepare_war_room_command_pack",
                    "prepare_founder_approval_brief",
                    "recommend_keep_upgrade_merge_remove",
                ),
                blocked_capabilities=(
                    "self_approval",
                    "production_deploy",
                    "production_database_migration",
                    "payment_capture",
                    "sika_money_transfer",
                    "real_world_dispatch",
                    "confirmed_reservation_claim",
                    "hidden_tracking",
                    "private_media_exposure",
                    "external_marketplace_authority",
                    "emergency_authority_claim",
                    "public_claim_without_proof",
                ),
                surfaces={
                    "oap_direct": {
                        "role": "Direct request, supplier/listing proof and reservation-readiness review.",
                        "booking_language": "OAP Direct",
                        "confirmation_locked": True,
                    },
                    "oap_atlas": {
                        "role": "Continent-to-postcode hierarchy and source-health review.",
                        "live_map_claim_locked_until_source_timestamp": True,
                    },
                    "movement": {
                        "role": "Route, request, consent, Link Up binding and movement-readiness review.",
                        "dispatch_locked": True,
                    },
                    "war_room": {
                        "role": "Operational command preparation, challenge, evidence scoring and escalation.",
                        "executes_real_world_actions": False,
                    },
                },
                proof_runner=proof,
            )
        )
    )
