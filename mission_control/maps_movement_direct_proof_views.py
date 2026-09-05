"""Founder-only read-only routes for OAP Atlas + Movement + Direct proof runner."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template, request

from . import maps_movement_direct_proof_runner, web_security

bp = Blueprint("maps_movement_direct_proof", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.app_errorhandler(404)
def clean_oap_not_found(error):
    """Return a quiet OAP fallback for unmatched paths without leaking private state."""

    wants_json = "application/json" in str(request.headers.get("Accept", ""))
    private_probe = request.path.startswith(
        ("/mission", "/my-world", "/myworld", "/infrastructure", "/api/infrastructure")
    )
    if wants_json:
        return _no_store(
            make_response(
                jsonify(
                    error={
                        "code": "oap_path_not_found",
                        "message": "This OAP path is not open.",
                        "private_state_exposed": False,
                        "private_probe": private_probe,
                        "safe_next": "/mission" if private_probe else "/",
                    }
                ),
                404,
            )
        )
    return _no_store(
        make_response(
            render_template("oap_404.html", private_probe=private_probe),
            404,
        )
    )


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


@bp.get("/war-room/smi-level/a5/atlas-movement-direct")
@bp.get("/war-room/actions/smi-level-a5-atlas-movement-direct")
# Quiet compatibility aliases from the old noisy route names.
@bp.get("/war-room/actions/a5-atlas-movement-direct")
@bp.get("/war-room/actions/a5-direct-atlas-movement")
@bp.get("/war-room/a5/atlas-movement-direct")
@web_security.login_required(api=True)
def smi_level_a5_atlas_movement_direct_projection():
    """Expose SMI Level A5 capability without treating A5 as a separate system."""

    proof = maps_movement_direct_proof_runner.status()
    return _no_store(
        make_response(
            jsonify(
                action_id="smi-level-a5-atlas-movement-direct",
                label="SMI Level A5 · OAP Atlas + Movement + OAP Direct",
                state="level_locked",
                signal="yellow",
                message=(
                    "SMI is the intelligence. A5 is only the governed autonomy level. "
                    "At Level A5, SMI may review, score and prepare command packs for "
                    "OAP Atlas, Movement and OAP Direct. It still cannot self-approve, "
                    "deploy, spend, dispatch, track hidden location, expose private media "
                    "or confirm reservations."
                ),
                public=False,
                founder_only=True,
                no_fake_green=True,
                intelligence="SMI",
                level="A5",
                level_name="Governed operational preparation",
                current_live_level="A4 supervised",
                next_levels={
                    "A6": {
                        "name": "Governed operational execution",
                        "state": "future_locked",
                        "requires": (
                            "independent proof runner results",
                            "Guardian pass",
                            "Green Gate pass",
                            "HRM receipts",
                            "Founder approval",
                            "rollback path",
                        ),
                    },
                    "A7": {
                        "name": "Certified organism-scale autonomy",
                        "state": "constitutional_locked",
                        "requires": (
                            "all A6 requirements",
                            "external audit",
                            "legal/compliance proof",
                            "live observability",
                            "emergency halt proof",
                            "no public/private boundary drift",
                        ),
                    },
                },
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


@bp.get("/smi/debug")
@bp.get("/war-room/smi/debug")
@bp.get("/war-room/actions/smi-debug")
@web_security.login_required(api=True)
def private_smi_debug_projection():
    """Return safe private SMI debug state without secrets, logs or private records."""

    proof = maps_movement_direct_proof_runner.status()
    route_matrix = dict(proof.get("route_matrix") or {})
    summary = dict(proof.get("summary") or {})
    return _no_store(
        make_response(
            jsonify(
                component="SMI Debug",
                public=False,
                founder_only=True,
                safe_for_screen=True,
                secrets_exposed=False,
                private_records_exposed=False,
                smi_public_exposure_blocked=True,
                active_level="A4 supervised",
                next_level="A5 locked level",
                signals_core=21,
                route_matrix={
                    "target_count": route_matrix.get("target_count"),
                    "public_target_count": route_matrix.get("public_target_count"),
                    "private_target_count": route_matrix.get("private_target_count"),
                    "live_capture_present": route_matrix.get("live_capture_present"),
                    "anonymous_capture_present": route_matrix.get("anonymous_capture_present"),
                    "certified": route_matrix.get("certified"),
                },
                proof_summary=summary,
                buttons={
                    "real_action_required": True,
                    "locked_state_allowed": True,
                    "fake_button_green_allowed": False,
                },
                hard_locks={
                    "self_approval": False,
                    "payment_capture": False,
                    "real_world_dispatch": False,
                    "confirmed_reservation_claim": False,
                    "hidden_tracking": False,
                    "private_media_exposure": False,
                    "public_claim_without_proof": False,
                },
            )
        )
    )
