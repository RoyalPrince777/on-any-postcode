#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

REPO_DIR="${OAP_HOME_REPO:-$HOME/on-any-postcode}"
ENV_FILE="${OAP_HOME_ENV:-$HOME/.config/oap/home-node.env}"
STATE_DIR="${OAP_HOME_STATE:-$HOME/.local/state/oap-home-node}"
VENV_DIR="${OAP_HOME_VENV:-$REPO_DIR/.venv}"
LOCK_DIR="$STATE_DIR/lock"
ORGANISM_LOG="$STATE_DIR/organism-worker.log"
INFERENCE_LOG="$STATE_DIR/inference-worker.log"

mkdir -p "$STATE_DIR"
umask 077

[[ -d "$REPO_DIR/.git" ]] || { echo "OAP Home Node refused: repository missing at $REPO_DIR" >&2; exit 2; }
[[ -f "$ENV_FILE" ]] || { echo "OAP Home Node refused: private environment file missing at $ENV_FILE" >&2; exit 2; }
[[ -x "$VENV_DIR/bin/python" ]] || { echo "OAP Home Node refused: Python environment missing at $VENV_DIR" >&2; exit 2; }

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  existing_pid="$(cat "$LOCK_DIR/pid" 2>/dev/null || true)"
  if [[ -n "$existing_pid" ]] && kill -0 "$existing_pid" 2>/dev/null; then
    echo "OAP Home Node already running as PID $existing_pid"
    exit 0
  fi
  rm -rf "$LOCK_DIR"
  mkdir "$LOCK_DIR"
fi
printf '%s\n' "$$" > "$LOCK_DIR/pid"

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

if [[ -z "${OAP_NEON_DATABASE_URL:-${DATABASE_URL:-}}" && -z "${OAP_DB_SECRET_B64:-${OAP_NEON_DATABASE_URL_B64:-}}" ]]; then
  echo "OAP Home Node refused: Neon database credential is not configured" >&2
  rm -rf "$LOCK_DIR"
  exit 2
fi
bridge_secret="${OAP_HOME_NODE_BRIDGE_SECRET:-}"
if (( ${#bridge_secret} < 32 )); then
  echo "OAP Home Node refused: OAP_HOME_NODE_BRIDGE_SECRET is not configured" >&2
  rm -rf "$LOCK_DIR"
  exit 2
fi

cd "$REPO_DIR"
export OAP_WORKER_ID="${OAP_WORKER_ID:-termux-$(hostname 2>/dev/null || echo android)}"
export OAP_ENV_REVISION="$(git rev-parse --short=12 HEAD 2>/dev/null || printf '%s' 'termux-unknown')"
export OAP_HOME_NODE_BRIDGE_URL="${OAP_HOME_NODE_BRIDGE_URL:-https://oap-smi.onrender.com/mission}"

termux-wake-lock >/dev/null 2>&1 || true

organism_pid=""
inference_pid=""

start_organism() {
  printf '%s starting organism worker revision=%s\n' "$(date -u +%FT%TZ)" "$OAP_ENV_REVISION" >> "$ORGANISM_LOG"
  "$VENV_DIR/bin/python" -m mission_control.organism_worker >> "$ORGANISM_LOG" 2>&1 &
  organism_pid="$!"
  printf '%s\n' "$organism_pid" > "$LOCK_DIR/organism.pid"
}

start_inference() {
  printf '%s starting inference worker revision=%s\n' "$(date -u +%FT%TZ)" "$OAP_ENV_REVISION" >> "$INFERENCE_LOG"
  "$VENV_DIR/bin/python" "$REPO_DIR/scripts/oap_home_node_inference_worker.py" >> "$INFERENCE_LOG" 2>&1 &
  inference_pid="$!"
  printf '%s\n' "$inference_pid" > "$LOCK_DIR/inference.pid"
}

cleanup() {
  trap - EXIT INT TERM
  for pid in "$organism_pid" "$inference_pid"; do
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      kill -TERM "$pid" 2>/dev/null || true
    fi
  done
  [[ -z "$organism_pid" ]] || wait "$organism_pid" 2>/dev/null || true
  [[ -z "$inference_pid" ]] || wait "$inference_pid" 2>/dev/null || true
  rm -rf "$LOCK_DIR"
  termux-wake-unlock >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

start_organism
start_inference

while true; do
  if ! kill -0 "$organism_pid" 2>/dev/null; then
    wait "$organism_pid" 2>/dev/null || true
    sleep 5
    start_organism
  fi
  if ! kill -0 "$inference_pid" 2>/dev/null; then
    wait "$inference_pid" 2>/dev/null || true
    sleep 5
    start_inference
  fi
  sleep 3
done
