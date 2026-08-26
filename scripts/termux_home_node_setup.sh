#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

REPO_URL="https://github.com/RoyalPrince777/on-any-postcode.git"
REPO_DIR="${OAP_HOME_REPO:-$HOME/on-any-postcode}"
ENV_DIR="$HOME/.config/oap"
ENV_FILE="$ENV_DIR/home-node.env"
STATE_DIR="$HOME/.local/state/oap-home-node"
BOOT_DIR="$HOME/.termux/boot"
BOOT_FILE="$BOOT_DIR/10-oap-home-node"

printf '%s\n' "OAP Home Node setup: bounded OAP CORE + SMI + whole-organism autonomy"
printf '%s\n' "No deploy, payment, dispatch, permission, carrier, or other consequential authority is enabled."

# Android/Termux has no compatible psycopg-binary wheel. The Home Node does not
# need the Render/web authentication dependency set, so use system libpq plus
# Psycopg's pure-Python implementation only.
pkg install -y python git postgresql

if [[ -d "$REPO_DIR/.git" ]]; then
  printf 'Using existing repository: %s\n' "$REPO_DIR"
elif [[ -e "$REPO_DIR" ]]; then
  printf 'Refusing to overwrite non-repository path: %s\n' "$REPO_DIR" >&2
  exit 2
else
  git clone --branch main --single-branch "$REPO_URL" "$REPO_DIR"
fi

cd "$REPO_DIR"
python -m venv .venv
PYTHON="$REPO_DIR/.venv/bin/python"
"$PYTHON" -m pip install --upgrade pip
"$PYTHON" -m pip install -r "$REPO_DIR/requirements-termux-home-node.txt"

original_ld_library_path="${LD_LIBRARY_PATH:-}"
termux_lib_path="$PREFIX/lib${original_ld_library_path:+:$original_ld_library_path}"
export LD_LIBRARY_PATH="$termux_lib_path"
PSYCOPG_IMPL=python "$PYTHON" - <<'PY'
import sys

import psycopg
from psycopg import pq

if pq.__impl__ != "python":
    raise SystemExit(f"Unexpected Psycopg implementation: {pq.__impl__}")

import mission_control.organism_worker  # noqa: E402

for forbidden in ("flask", "jwt", "cryptography"):
    if forbidden in sys.modules:
        raise SystemExit(f"Worker preflight unexpectedly loaded web dependency: {forbidden}")

print(f"Psycopg ready via {pq.__impl__} implementation; libpq={pq.version()}")
print("OAP Home Node worker preflight passed without Flask/JWT/cryptography")
PY

mkdir -p "$ENV_DIR" "$STATE_DIR" "$BOOT_DIR"
umask 077

printf '%s' "Paste the production Neon PostgreSQL URL (input is hidden): "
IFS= read -r -s database_url
printf '\n'
case "$database_url" in
  postgresql://*|postgres://*) ;;
  *)
    printf '%s\n' "Refused: expected a PostgreSQL connection URL." >&2
    exit 2
    ;;
esac

worker_id="termux-$(hostname 2>/dev/null || printf '%s' android)"
{
  printf 'export OAP_NEON_DATABASE_URL=%q\n' "$database_url"
  printf 'export OAP_WORKER_ID=%q\n' "$worker_id"
  printf 'export OAP_HOME_REPO=%q\n' "$REPO_DIR"
  printf 'export PSYCOPG_IMPL=python\n'
  printf 'export LD_LIBRARY_PATH=%q\n' "$termux_lib_path"
} > "$ENV_FILE"
chmod 600 "$ENV_FILE"
unset database_url

cat > "$BOOT_FILE" <<EOF
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock >/dev/null 2>&1 || true
nohup "$REPO_DIR/scripts/termux_home_node_run.sh" >> "$STATE_DIR/boot.log" 2>&1 &
EOF
chmod 700 "$BOOT_FILE"
chmod 700 "$REPO_DIR/scripts/termux_home_node_run.sh"
chmod 700 "$REPO_DIR/scripts/termux_home_node_status.sh"

printf '%s\n' "Setup complete."
printf '%s\n' "1. Install/open Termux:Boot once if you have not already."
printf '%s\n' "2. Set Android battery usage for Termux and Termux:Boot to Unrestricted."
printf '%s\n' "3. Start now with: $REPO_DIR/scripts/termux_home_node_run.sh"
printf '%s\n' "4. Check status with: $REPO_DIR/scripts/termux_home_node_status.sh"
printf '%s\n' "The runner does not auto-pull code. Updates remain an explicit Human Authority action."
