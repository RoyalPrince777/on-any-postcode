#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

REPO_DIR="${OAP_HOME_REPO:-$HOME/on-any-postcode}"
ENV_FILE="${OAP_HOME_ENV:-$HOME/.config/oap/home-node.env}"
STATE_DIR="${OAP_HOME_STATE:-$HOME/.local/state/oap-home-node}"
LOCK_DIR="$STATE_DIR/lock"
VENV_DIR="${OAP_HOME_VENV:-$REPO_DIR/.venv}"

pid_state() {
  local file="$1"
  if [[ -f "$file" ]]; then
    local pid
    pid="$(cat "$file" 2>/dev/null || true)"
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      printf '%s' running
      return
    fi
  fi
  printf '%s' stopped
}

printf 'home_node_process=%s\n' "$(pid_state "$LOCK_DIR/pid")"
printf 'organism_worker=%s\n' "$(pid_state "$LOCK_DIR/organism.pid")"
printf 'inference_worker=%s\n' "$(pid_state "$LOCK_DIR/inference.pid")"

if [[ ! -f "$ENV_FILE" || ! -x "$VENV_DIR/bin/python" ]]; then
  printf '%s\n' "runtime_status=unavailable"
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
cd "$REPO_DIR"

bridge_secret="${OAP_HOME_NODE_BRIDGE_SECRET:-}"
printf 'bridge_secret_configured=%s\n' "$([[ ${#bridge_secret} -ge 32 ]] && echo true || echo false)"
"$VENV_DIR/bin/python" - <<'PY'
import json
from mission_control.organism_runtime import runtime_status
print(json.dumps(runtime_status(), indent=2, sort_keys=True))
PY
