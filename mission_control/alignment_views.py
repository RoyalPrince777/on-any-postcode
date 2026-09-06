"""Founder-only SMI alignment, simulation and master upgrade routes."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, request

from . import (
    ai_behaviour_protocol,
    alignment_check,
    master_upgrade_contract,
    smi_brain_evidence_protocol,
    smi_brain_evidence_runner,
    smi_brain_protocol,
    smi_brain_score21,
    smi_completion_contract,
    smi_deep_dive_protocol,
    smi_receipt_backend,
    war_room_simulation_actions,
    web_security,
)

bp = Blueprint("alignment", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.get("/war-room/deep-dive")
@bp.get("/war-room/actions/deep-dive")
@bp.get("/smi/deep-dive")
@web_security.login_required(api=True, founder_only=True)
def smi_deep_dive_status():
    """Return the Founder-only SMI-first Deep-Dive Simulation Protocol."""

    return _no_store(make_response(jsonify(smi_deep_dive_protocol.status())))


@bp.get("/war-room/deep-dive/simulate")
@bp.get("/war-room/actions/deep-dive-simulate")
@bp.get("/smi/deep-dive/simulate")
@web_security.login_required(api=True, founder_only=True)
def smi_deep_dive_simulate():
    """Return a bounded SMI-first simulation frame for one command."""

    return _no_store(
        make_response(
            jsonify(
                smi_deep_dive_protocol.simulate(
                    request.args.get("command"), request.args.get("agent")
                )
            )
        )
    )


@bp.get("/war-room/smi-brain/evidence")
@bp.get("/war-room/actions/smi-brain-evidence")
@bp.get("/smi/brain/evidence")
@web_security.login_required(api=True, founder_only=True)
def smi_brain_evidence_status():
    """Return the Founder-only SMI Brain 14 x 7 evidence completion protocol."""

    return _no_store(make_response(jsonify(smi_brain_evidence_protocol.completion_check(request.args.get("part")))))


@bp.get("/war-room/smi-brain/evidence-runner")
@bp.get("/war-room/actions/smi-brain-evidence-runner")
@bp.get("/smi/brain/evidence-runner")
@web_security.login_required(api=True, founder_only=True)
def smi_brain_evidence_runner_status():
    """Return the Founder-only SMI Brain live evidence runner catalogue."""

    return _no_store(make_response(jsonify(smi_brain_evidence_runner.runner_status())))


@bp.get("/war-room/smi-brain/evidence-runner/run")
@bp.get("/war-room/actions/smi-brain-evidence-runner-run")
@bp.get("/smi/brain/evidence-runner/run")
@web_security.login_required(api=True, founder_only=True)
def smi_brain_evidence_runner_run():
    """Run a bounded Founder-only evidence proof check without external execution."""

    return _no_store(
        make_response(
            jsonify(
                smi_brain_evidence_runner.run(
                    part=request.args.get("part"),
                    gate=request.args.get("gate"),
                    command=request.args.get("command"),
                )
            )
        )
    )


@bp.get("/war-room/smi-brain/receipts")
@bp.get("/war-room/actions/smi-brain-receipts")
@bp.get("/smi/brain/receipts")
@web_security.login_required(api=True, founder_only=True)
def smi_brain_receipts():
    """Return private-safe SMI receipt backend status and recent receipt headers."""

    limit = request.args.get("limit", "20")
    try:
        safe_limit = max(1, min(int(limit), 100))
    except ValueError:
        safe_limit = 20
    return _no_store(
        make_response(
            jsonify(
                {
                    "status": smi_receipt_backend.receipt_backend_status(),
                    "latest": smi_receipt_backend.latest_receipts(safe_limit),
                }
            )
        )
    )


@bp.get("/war-room/smi-brain")
@bp.get("/war-room/actions/smi-brain")
@bp.get("/smi/brain/status")
@web_security.login_required(api=True, founder_only=True)
def smi_brain_status():
    """Return the Founder-only SMI Brain 14 x 7 status board."""

    return _no_store(make_response(jsonify(smi_brain_protocol.brain_status())))


@bp.get("/war-room/smi-brain/simulate")
@bp.get("/war-room/actions/smi-brain-simulate")
@bp.get("/smi/brain/simulate")
@web_security.login_required(api=True, founder_only=True)
def smi_brain_simulation():
    """Start the safe War Room simulation for the 14 brain parts up to 7/7."""

    return _no_store(
        make_response(jsonify(smi_brain_protocol.simulation(request.args.get("stage"))))
    )


@bp.get("/war-room/smi-brain/score")
@bp.get("/war-room/actions/smi-brain-score")
@bp.get("/smi/brain/score")
@web_security.login_required(api=True, founder_only=True)
def smi_brain_score():
    """Return the Founder-only 3 + 7 + 7 = 17/21 SMI Brain score."""

    return _no_store(make_response(jsonify(smi_brain_score21.score21_status())))


@bp.get("/war-room/ai-behaviour")
@bp.get("/war-room/actions/ai-behaviour")
@bp.get("/smi/ai-behaviour")
@web_security.login_required(api=True, founder_only=True)
def ai_behaviour():
    """Return the Founder-only SMI AI behaviour protocol."""

    return _no_store(
        make_response(jsonify(ai_behaviour_protocol.status(request.args.get("target") or "SMI")))
    )


@bp.get("/war-room/master-upgrade")
@bp.get("/war-room/actions/master-upgrade")
@bp.get("/smi/master-upgrade")
@web_security.login_required(api=True, founder_only=True)
def master_upgrade():
    """Return the real-green master upgrade contract."""

    return _no_store(make_response(jsonify(master_upgrade_contract.status())))


@bp.get("/war-room/alignment")
@bp.get("/war-room/actions/alignment")
@bp.get("/alignment/status")
@web_security.login_required(api=True, founder_only=True)
def alignment_status():
    """Check public/menu alignment without exposing private state publicly."""

    return _no_store(make_response(jsonify(alignment_check.status())))


@bp.get("/war-room/thinking-signals")
@bp.get("/war-room/actions/thinking-signals")
@bp.get("/smi/thinking-signals")
@web_security.login_required(api=True, founder_only=True)
def thinking_signals():
    """Return private-safe visible SMI thinking/status signals."""

    return _no_store(make_response(jsonify(alignment_check.thinking_signals())))


@bp.get("/war-room/smi-completion")
@bp.get("/war-room/actions/smi-completion")
@bp.get("/smi/completion")
@web_security.login_required(api=True, founder_only=True)
def smi_completion():
    """Return the private-safe SMI completion contract."""

    return _no_store(make_response(jsonify(smi_completion_contract.completion_status())))


@bp.get("/war-room/simulation-actions")
@bp.get("/war-room/actions/simulation-actions")
@bp.get("/smi/simulation-actions")
@web_security.login_required(api=True, founder_only=True)
def simulation_actions():
    """Return the Founder-only War Room dry-run action catalogue."""

    return _no_store(make_response(jsonify(war_room_simulation_actions.list_actions())))


@bp.get("/war-room/simulate")
@bp.get("/war-room/actions/simulate")
@bp.get("/smi/simulate")
@web_security.login_required(api=True, founder_only=True)
def simulate_action():
    """Run one safe dry-run simulation without executing external action."""

    return _no_store(
        make_response(
            jsonify(
                war_room_simulation_actions.simulate(
                    request.args.get("action"),
                    request.args.get("target"),
                    request.args.get("stage", "auto"),
                )
            )
        )
    )


@bp.get("/war-room/debug/simple-task")
@bp.get("/war-room/actions/simple-task-debug")
@web_security.login_required(api=True, founder_only=True)
def simple_task_debug():
    """Return the safe protocol for a simple task fix/debug loop."""

    return _no_store(
        make_response(
            jsonify(alignment_check.simple_task_debug(request.args.get("task")))
        )
    )


@bp.get("/war-room/debug/404")
@bp.get("/war-room/actions/404-check")
@web_security.login_required(api=True, founder_only=True)
def not_found_debug():
    """Return the private-safe 404 recovery check."""

    pack = alignment_check.simple_task_debug("404 public recovery check")
    pack["checks"] = {
        "public_404_simple": True,
        "public_404_has_private_debug": False,
        "public_404_routes": ("/", "/on-any-place", "/movement", "/travel/direct"),
        "war_room_owns_debug": True,
    }
    return _no_store(make_response(jsonify(pack)))
