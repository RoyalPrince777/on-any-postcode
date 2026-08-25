"""Network-facing boundary between public OAP and private SMI surfaces."""
from __future__ import annotations

import hmac
import os

from flask import Flask, make_response, request

_GATEWAY_HEADER = "X-OAP-SMI-Gateway"


def gateway_configured() -> bool:
    return bool(os.environ.get("OAP_SMI_GATEWAY_SECRET", "").strip())


def gateway_authorized() -> bool:
    expected = os.environ.get("OAP_SMI_GATEWAY_SECRET", "").strip()
    supplied = request.headers.get(_GATEWAY_HEADER, "")
    return bool(expected and supplied) and hmac.compare_digest(expected, supplied)


def register(app: Flask) -> None:
    """Hide Mission Control from the public origin once a gateway is configured.

    The check intentionally returns 404 rather than advertising that a private
    surface exists. Before the secret is configured, behavior remains backward
    compatible so deployment can be staged without locking out Human Authority.
    """

    @app.before_request
    def _enforce_smi_gateway():
        path = request.path.rstrip("/") or "/"
        if path != "/mission" and not path.startswith("/mission/"):
            return None
        if not gateway_configured() or gateway_authorized():
            return None
        response = make_response("", 404)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response
