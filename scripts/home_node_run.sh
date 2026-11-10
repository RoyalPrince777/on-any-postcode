#!/usr/bin/env bash
set -Eeuo pipefail
REPO_DIR="${OAP_HOME_REPO:-$HOME/on-any-postcode}"
ENV_FILE="${OAP_HOME_ENV:-$HOME/.config/oap/home-node.env}"
VENV_DIR="${OAP_HOME_VENV:-$REPO_DIR/.venv}"
[[ -d "$REPO_DIR/.git" ]] || { echo "Home Node repo missing: $REPO_DIR" >&2; exit 2; }
[[ -x "$VENV_DIR/bin/python" ]] || { echo "Home Node Python missing: $VENV_DIR" >&2; exit 2; }
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi
cd "$REPO_DIR"
export OAP_HOME_REPO="$REPO_DIR"
export OAP_ENV_REVISION="$(git rev-parse --short=12 HEAD 2>/dev/null || echo device-local)"
exec "$VENV_DIR/bin/python" "$REPO_DIR/scripts/oap_home_node_supervisor.py"
