#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

REPO_DIR="${OAP_HOME_REPO:-$HOME/on-any-postcode}"
ENV_FILE="${OAP_HOME_ENV:-$HOME/.config/oap/home-node.env}"
VENV_DIR="${OAP_HOME_VENV:-$REPO_DIR/.venv}"

[[ -d "$REPO_DIR/.git" ]] || { echo "OAP Home Node refused: repository missing at $REPO_DIR" >&2; exit 2; }
[[ -f "$ENV_FILE" ]] || { echo "OAP Home Node refused: private environment file missing at $ENV_FILE" >&2; exit 2; }
[[ -x "$VENV_DIR/bin/python" ]] || { echo "OAP Home Node refused: Python environment missing at $VENV_DIR" >&2; exit 2; }

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

cd "$REPO_DIR"
export OAP_WORKER_ID="${OAP_WORKER_ID:-termux-$(hostname 2>/dev/null || echo android)}"
export OAP_ENV_REVISION="$(git rev-parse --short=12 HEAD 2>/dev/null || echo termux-unknown)"

termux-wake-lock >/dev/null 2>&1 || true
cleanup() {
  termux-wake-unlock >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

exec "$VENV_DIR/bin/python" "$REPO_DIR/scripts/oap_home_node_supervisor.py"
