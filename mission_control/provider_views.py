"""Private Mission Control views for Provider Fabric and alignment truth."""

from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template
from oap.smi import intelligence_capability_registry, sovereign_controls

from . import agents as agent_registry
from . import autonomy_levels, provider_fabric, web_security

bp = Blueprint("provider_fabric", __name__, template_folder="templates")


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.get("/providers")
@web_security.login_required()
def provider_dashboard():
    """Render provider readiness without exposing credentials or controls."""

    response = make_response(
        render_template(
            "provider_fabric.html",
            fabric=provider_fabric.get_private_provider_fabric(),
        )
    )
    return _no_store(response)


@bp.get("/providers/status")
@web_security.login_required(api=True)
def provider_status():
    """Return coarse provider readiness only to a signed-in identity."""

    return _no_store(make_response(jsonify(provider_fabric.get_coarse_provider_status())))


@bp.get("/alignment")
@web_security.login_required(founder_only=True)
def alignment_dashboard():
    """Render evidence-based SMI alignment and technical sovereignty state."""

    sovereignty = sovereign_controls.SovereignControlPlane().status()
    capability_registry = intelligence_capability_registry.status(
        agent_registry.LOCKED_WORLD_IDS
    )
    autonomy = autonomy_levels.status()
    response = make_response(
        render_template(
            "alignment_sovereignty.html",
            sovereignty=sovereignty,
            capability_registry=capability_registry,
            autonomy=autonomy,
            worlds=agent_registry.INTELLIGENCE_WORLDS,
            agent_count=agent_registry.LOCKED_AGENT_COUNT,
        )
    )
    return _no_store(response)


@bp.get("/alignment/status")
@web_security.login_required(api=True, founder_only=True)
def alignment_status():
    """Return the same redacted alignment evidence for private status polling."""

    sovereignty = sovereign_controls.SovereignControlPlane().status()
    capability_registry = intelligence_capability_registry.status(
        agent_registry.LOCKED_WORLD_IDS
    )
    autonomy = autonomy_levels.status()
    return _no_store(
        make_response(
            jsonify(
                single_smi_brain=True,
                world_count=len(agent_registry.INTELLIGENCE_WORLDS),
                agent_count=agent_registry.LOCKED_AGENT_COUNT,
                capability_count=capability_registry["capability_count"],
                capability_alignment=capability_registry["validation"]["passed"],
                autonomy=autonomy,
                sovereignty=sovereignty,
                provider_authority=False,
                human_authority_final=True,
            )
        )
    )
