#!/usr/bin/env bash
# Founder-owned, same-device full OAP Core Flask route registry. NOT a public deployment.
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
# Load a separately provisioned Founder-only auth configuration when available.
# Never generate, echo, overwrite, or transmit credentials during recovery.
founder_env="$HOME/.config/oap/smi-founder.env"
if [[ -e "$founder_env" ]]; then
  if [[ ! -f "$founder_env" || ! -O "$founder_env" || ! -r "$founder_env" ]]; then
    echo "SMI_FLASK_FOUNDER_CONFIG_INACCESSIBLE" >&2
    exit 2
  fi
  founder_mode="$(stat -c '%a' "$founder_env")"
  if [[ "$founder_mode" != "600" && "$founder_mode" != "400" ]]; then
    echo "SMI_FLASK_FOUNDER_CONFIG_PERMISSIONS: require chmod 600" >&2
    exit 2
  fi
  set -a
  . "$founder_env"
  set +a
fi
export OAP_LOCAL_MODE=true
export OAP_SURFACE_ROLE=local
export OAP_SMI_GATEWAY_SECRET=
export OAP_PRIVATE_SMI_ORIGIN=
export OAP_AUTH_REQUIRED=true
export FLASK_DEBUG=0
export PYTHONUNBUFFERED=1

# The existing Home Node worker venv deliberately omits Flask and web/auth
# dependencies. Prefer a separately provisioned OAP Core environment when set;
# otherwise use the current Python. Never pip-install or replace worker packages
# implicitly while starting the Founder application.
core_python="${OAP_CORE_PYTHON:-python}"
if ! command -v "$core_python" >/dev/null 2>&1; then
  echo "OAP_CORE_PYTHON_UNAVAILABLE: provision the full Core runtime separately" >&2
  exit 2
fi
if ! "$core_python" - <<'CHECK'
from importlib.util import find_spec
required = ("flask", "jwt", "pyotp", "psycopg", "qrcode", "slowapi", "starlette")
missing = [package for package in required if find_spec(package) is None]
if missing:
    raise SystemExit("OAP_CORE_DEPENDENCIES_MISSING: " + ", ".join(missing))
CHECK
then
  echo "OAP Core local startup refused; worker-only Termux requirements are insufficient." >&2
  exit 2
fi

exec "$core_python" - <<'PY'
import os
from app import app
from mission_control import surface_security
from mission_control import neon_auth, postgres_db
from mission_control import founder_local_auth, founder_recovery

# Refuse to advertise a working SMI login when neither existing identity
# backend is configured. No recovery token, identity, or password is generated.
database_ready = postgres_db.configured()
auth_backend = neon_auth.status()["valid"]
auth_origin = bool(neon_auth.configured_public_origin())
founder_selector = bool(neon_auth.configured_founder_email())
local_session_ready = len(os.environ.get("OAP_SESSION_SECRET", "")) >= 32
local_verifier_bound = bool(local_session_ready and founder_local_auth.bound())
recovery_ready = founder_recovery.configured()
managed_ready = auth_backend and auth_origin and founder_selector
print("SMI database configuration:", "present; connection unverified" if database_ready else "missing")
print("SMI managed auth endpoint:", "configured" if auth_backend else "missing")
print("SMI managed auth HTTPS origin:", "configured; trust unverified" if auth_origin else "missing")
print("SMI Founder selector:", "configured" if founder_selector else "missing")
print("SMI Founder verifier:", "verified bound; login still required" if local_verifier_bound else "not proven")
print("SMI existing recovery:", "configured" if recovery_ready else "unavailable")
if not (managed_ready or local_verifier_bound or recovery_ready):
    print("SMI NEXT ACTION: provision approved Founder settings in ~/.config/oap/smi-founder.env (chmod 600).")
    print("SMI BLOCKER: no verified Founder authentication route is available. Existing password unchanged.")
    raise SystemExit("SMI_FLASK_AUTH_NOT_CONFIGURED: restore existing Founder auth and trusted HTTPS origin; password unchanged")

# The canonical app owns ALL registered OAP routes: do not fork or proxy them
# through Render or a duplicate Termux router.
required_routes = ("/", "/world", "/mission/ollama")
registered = {rule.rule for rule in app.url_map.iter_rules() if "GET" in rule.methods}
missing = [path for path in required_routes if path not in registered]
if missing:
    raise SystemExit("OAP_CORE_LOCAL_ROUTES_MISSING: " + ", ".join(missing))
route = "/mission/ollama"
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
# 5050 is the canonical local OAP Core entrypoint on the Founder device.
# Bind loopback only; internet access requires separate verified first-party TLS
# ingress and a security review. Never publish this Flask development server.
port = 5050
print("OAP Core local route registry:", len(list(app.url_map.iter_rules())), "registered rules")
print("Open OAP World: http://127.0.0.1:5050/world")
print("Open SMI: http://127.0.0.1:5050/mission/ollama")
print("Founder authentication remains enforced. No external network binding.")
app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)
PY
