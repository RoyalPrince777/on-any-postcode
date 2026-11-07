#!/data/data/com.termux/files/usr/bin/bash
# Install full OAP Flask Core separately from the existing Home Node worker.
# No auto-pull, secrets, DB migrations, boot registration, public bind or deploy.
set -Eeuo pipefail
REPO_DIR="${OAP_HOME_REPO:-$HOME/on-any-postcode}"
[[ -d "$REPO_DIR/.git" ]] || { echo "OAP_CORE_REPO_MISSING" >&2; exit 2; }
cd "$REPO_DIR"
[[ -f requirements-termux-core.txt ]] || { echo "OAP_CORE_REQUIREMENTS_MISSING" >&2; exit 2; }
[[ -n "${PREFIX:-}" && "$PREFIX" == */com.termux/files/usr ]] || {
  echo "OAP_CORE_TERMUX_REQUIRED" >&2; exit 2;
}
# Native build tools are required for Android wheels such as cryptography.
pkg install -y python clang rust pkg-config openssl libffi postgresql
if [[ -e .venv-core && ! -x .venv-core/bin/python ]]; then
  echo "OAP_CORE_ENV_INVALID: refusing to overwrite existing path" >&2
  exit 2
fi
if [[ ! -x .venv-core/bin/python ]]; then python -m venv .venv-core; fi
core_python="$REPO_DIR/.venv-core/bin/python"
# The existing .venv remains untouched; no global packages or automatic upgrades.
PSYCOPG_IMPL=python "$core_python" -m pip install -r requirements-termux-core.txt
export LD_LIBRARY_PATH="$PREFIX/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
PSYCOPG_IMPL=python "$core_python" - <<'PY'
import importlib
from psycopg import pq
modules = ("flask", "jwt", "cryptography", "pyotp", "psycopg", "qrcode",
           "slowapi", "starlette", "mapbox_vector_tile")
for name in modules:
    importlib.import_module(name)
if pq.__impl__ != "python":
    raise SystemExit("OAP_CORE_PSYCOPG_IMPL_UNEXPECTED")
print("OAP_CORE_IMPORT_PREFLIGHT_PASSED; Flask routes and Founder auth still require runtime proof")
PY
printf '%s\n' "OAP Core environment installed separately; no application started."
printf '%s\n' "To start after approved Founder auth configuration:"
printf '  OAP_CORE_PYTHON=%q bash scripts/smi_local_flask.sh\n' "$core_python"
