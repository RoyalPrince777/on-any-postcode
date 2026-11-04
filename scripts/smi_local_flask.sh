#!/usr/bin/env bash
# Founder-owned, same-device Flask entry point. This is NOT a public deployment.
set -Eeuo pipefail
cd "$(dirname "$0")/.."
export OAP_LOCAL_MODE=true
export OAP_SURFACE_ROLE=local
export OAP_SMI_GATEWAY_SECRET=
export OAP_PRIVATE_SMI_ORIGIN=
export OAP_AUTH_REQUIRED=true
export FLASK_DEBUG=0
export PYTHONUNBUFFERED=1

exec python - <<'PY'
import os
from app import app
from mission_control import surface_security

route = "/mission/ollama"
registered = any(rule.rule == route and "GET" in rule.methods for rule in app.url_map.iter_rules())
if not registered:
    raise SystemExit("SMI_FLASK_ROUTE_NOT_REGISTERED: check installed branch")
if surface_security.public_surface_enforced() or surface_security.gateway_configured():
    raise SystemExit("SMI_FLASK_PRIVATE_BOUNDARY_NOT_LOCAL")
if app.config.get("TESTING") or app.debug:
    raise SystemExit("SMI_FLASK_DEBUG_OR_TEST_MODE_NOT_ALLOWED")
with app.test_client() as client:
    response = client.get(route, follow_redirects=False)
    if response.status_code == 404:
        raise SystemExit("SMI_FLASK_PREFLIGHT_404: private route is blocked; check app state")
    # The actual Founder session remains necessary. Never auto-login or supply test authority.
    if response.status_code not in (302, 303, 401, 403, 503):
        raise SystemExit(f"SMI_FLASK_UNEXPECTED_AUTH_GATE_{response.status_code}")
    print(f"SMI Flask preflight: route registered; auth response {response.status_code}")
print("Open on this device: http://127.0.0.1:5051/mission/ollama")
print("Founder authentication remains enforced. No external network binding.")
app.run(host="127.0.0.1", port=5051, debug=False, use_reloader=False)
PY
