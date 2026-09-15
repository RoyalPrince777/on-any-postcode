"""Mission Control package initialiser.

Web-only dependencies are imported inside ``init_app`` so worker-only runtimes
such as the Termux OAP Home Node can import ``mission_control.organism_worker``
without installing Flask, PyJWT crypto extras, or other HTTP surface packages.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Flask


def init_app(app: Flask) -> None:
    """Register the Mission Control web surface needed by the SMI gateway."""
    from flask import g, request

    from . import smi_auto, surface_security
    from .founder_tool_views import bp as founder_tool_bp
    from .hrm_certification_views import bp as hrm_certification_bp
    from .views import bp

    @app.before_request
    def _oap_smi_auto_observe() -> None:
        g.oap_smi_auto = smi_auto.observe(request.method, request.path, request.endpoint)

    @app.context_processor
    def _oap_smi_auto_context() -> dict[str, object]:
        return {"smi_auto": getattr(g, "oap_smi_auto", smi_auto.public_status())}

    @app.after_request
    def _oap_smi_auto_response(response):
        state = getattr(g, "oap_smi_auto", smi_auto.public_status())
        response.headers.setdefault("X-OAP-SMI-Auto", "active")
        response.headers.setdefault("X-OAP-SMI-Mode", str(state.get("mode", "automatic_low_noise")))
        response.headers.setdefault("X-OAP-SMI-War-Room", "escalate" if state.get("war_room_escalation") else "normal")
        response.headers.setdefault("X-OAP-SMI-Execution", "blocked")
        return response

    surface_security.register(app)
    app.register_blueprint(founder_tool_bp, url_prefix="/mission")
    app.register_blueprint(hrm_certification_bp, url_prefix="/mission")
    app.register_blueprint(bp, url_prefix="/mission")
