#!/usr/bin/env bash
# Founder-owned, same-device Flask entry point. This is NOT a public deployment.
set -Eeuo pipefail
cd "$(dirname "$0")/.."
# Reuse the already provisioned, owner-private Home Node configuration if present.
# Do not overwrite it or print its values.
home_env="$HOME/.config/oap/home-node.env"
if [[ -f "$home_env" ]]; then
  if [[ ! -O "$home_env" || ! -r "$home_env" ]]; then
    echo "SMI_FLASK_HOME_CONFIG_INACCESSIBLE" >&2
    exit 2
  fi
  set -a
  . "$home_env"
  set +a
fi
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
from mission_control import neon_auth, postgres_db
from mission_control import founder_recovery

# Refuse to advertise a working SMI login when neither existing identity
# backend is configured. No recovery token, identity, or password is generated.
database_ready = postgres_db.configured()
auth_backend = neon_auth.status()["valid"]
auth_origin = bool(neon_auth.configured_public_origin())
founder_selector = bool(neon_auth.configured_founder_email())
local_verifier_candidate = (database_ready and len(os.environ.get("OAP_SESSION_SECRET", "")) >= 32 and bool(os.environ.get("OAP_HUMAN_AUTHORITY_ID", "")))
recovery_ready = founder_recovery.configured()
managed_ready = auth_backend and auth_origin and founder_selector
print("SMI database configuration:", "present; connection unverified" if database_ready else "missing")
print("SMI managed auth endpoint:", "configured" if auth_backend else "missing")
print("SMI managed auth HTTPS origin:", "configured; trust unverified" if auth_origin else "missing")
print("SMI Founder selector:", "configured" if founder_selector else "missing")
print("SMI Founder verifier prerequisites:", "present; runtime unverified" if local_verifier_candidate else "missing")
print("SMI existing recovery:", "configured" if recovery_ready else "unavailable")
if not (managed_ready or local_verifier_candidate or recovery_ready):
    raise SystemExit("SMI_FLASK_AUTH_NOT_CONFIGURED: restore existing Founder auth and trusted HTTPS origin; password unchanged")

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
