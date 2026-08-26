#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

REPO_DIR="${OAP_HOME_REPO:-$HOME/on-any-postcode}"
ENV_FILE="${OAP_HOME_ENV:-$HOME/.config/oap/home-node.env}"
STATE_DIR="${OAP_HOME_STATE:-$HOME/.local/state/oap-home-node}"
VENV_DIR="${OAP_HOME_VENV:-$REPO_DIR/.venv}"
LOCK_DIR="$STATE_DIR/lock"
LOG_FILE="$STATE_DIR/worker.log"

mkdir -p "$STATE_DIR"
umask 077

if [[ ! -d "$REPO_DIR/.git" ]]; then
  echo "OAP Home Node refused: repository missing at $REPO_DIR" >&2
  exit 2
fi
if [[ ! -f "$ENV_FILE" ]]; then
  echo "OAP Home Node refused: private environment file missing at $ENV_FILE" >&2
  exit 2
fi
if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  echo "OAP Home Node refused: Python environment missing at $VENV_DIR" >&2
  exit 2
fi

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

cd "$REPO_DIR"
export OAP_WORKER_ID="${OAP_WORKER_ID:-termux-$(hostname 2>/dev/null || echo android)}"
export OAP_ENV_REVISION="$(git rev-parse --short=12 HEAD 2>/dev/null || printf '%s' 'termux-unknown')"

termux-wake-lock >/dev/null 2>&1 || true

child_pid=""
cleanup() {
  trap - EXIT INT TERM
  if [[ -n "$child_pid" ]] && kill -0 "$child_pid" 2>/dev/null; then
    kill -TERM "$child_pid" 2>/dev/null || true
    wait "$child_pid" 2>/dev/null || true
  fi
  rm -rf "$LOCK_DIR"
  termux-wake-unlock >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

backoff=15
while true; do
  started_at="$(date +%s)"
  printf '%s %s\n' "$(date -u +%FT%TZ)" "starting bounded organism worker revision=$OAP_ENV_REVISION" >> "$LOG_FILE"
  "$VENV_DIR/bin/python" -m mission_control.organism_worker >> "$LOG_FILE" 2>&1 &
  child_pid="$!"

  set +e
  wait "$child_pid"
  exit_code="$?"
  set -e
  child_pid=""

  stopped_at="$(date +%s)"
  runtime_seconds="$((stopped_at - started_at))"
  printf '%s worker exited code=%s runtime_seconds=%s\n' "$(date -u +%FT%TZ)" "$exit_code" "$runtime_seconds" >> "$LOG_FILE"

  if (( runtime_seconds >= 120 )); then
    backoff=15
  else
    backoff="$((backoff * 2))"
    if (( backoff > 300 )); then
      backoff=300
    fi
  fi
  sleep "$backoff"
done
