#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

REPO_DIR="${OAP_HOME_REPO:-$HOME/on-any-postcode}"
ENV_FILE="${OAP_HOME_ENV:-$HOME/.config/oap/home-node.env}"
VENV_DIR="${OAP_HOME_VENV:-$REPO_DIR/.venv}"

[[ -f "$ENV_FILE" ]] || { echo "runtime_status=unavailable"; exit 1; }
[[ -x "$VENV_DIR/bin/python" ]] || { echo "runtime_status=unavailable"; exit 1; }

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

cd "$REPO_DIR"
exec "$VENV_DIR/bin/python" "$REPO_DIR/scripts/oap_home_node_status.py"
