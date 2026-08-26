#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

REPO_DIR="${OAP_HOME_REPO:-$HOME/on-any-postcode}"
ENV_FILE="${OAP_HOME_ENV:-$HOME/.config/oap/home-node.env}"
STATE_DIR="${OAP_HOME_STATE:-$HOME/.local/state/oap-home-node}"
PID_FILE="$STATE_DIR/lock/pid"
VENV_DIR="${OAP_HOME_VENV:-$REPO_DIR/.venv}"

process_state="stopped"
if [[ -f "$PID_FILE" ]]; then
  pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    process_state="running"
  fi
fi
printf 'home_node_process=%s\n' "$process_state"

if [[ ! -f "$ENV_FILE" || ! -x "$VENV_DIR/bin/python" ]]; then
  printf '%s\n' "runtime_status=unavailable"
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
cd "$REPO_DIR"

"$VENV_DIR/bin/python" - <<'PY'
import json
from mission_control.organism_runtime import runtime_status

print(json.dumps(runtime_status(), indent=2, sort_keys=True))
PY
