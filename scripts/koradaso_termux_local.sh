#!/data/data/com.termux/files/usr/bin/bash
# KORADASO Internet: run the verified checkout without altering the main Termux tree.
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${OAP_KORADASO_PORT:-5052}"
if [[ "$PORT" != "5052" && "$PORT" != "5050" ]]; then
  echo "KORADASO refused: use only isolated test port 5052 or verified browser port 5050." >&2
  exit 2
fi
cd "$ROOT"
export OAP_LOCAL_MODE=true
if [[ "${OAP_SURFACE_ROLE:-}" == "public" ]]; then
  echo "KORADASO refused: public surface role cannot be repurposed as a local private runtime." >&2
  exit 2
fi
export FLASK_DEBUG=0

index_dir="${XDG_DATA_HOME:-$HOME/.local/share}/oap/koradaso"
index_path="${OAP_KORADASO_WEB_INDEX:-$index_dir/public-index.sqlite3}"

if [[ "${1:-}" == "--crawl" && "$#" -eq 1 ]]; then
  seeds="$(mktemp)"
  trap 'rm -f -- "$seeds"' EXIT
  python - scripts/koradaso_starter_pages.jsonl > "$seeds" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as source:
    for line in source:
        if line.strip():
            print(json.loads(line)["url"])
PY
  python scripts/koradaso_crawl_seeds.py --source "$seeds" --db "$index_path" --execute
  exit
fi
if (( $# )); then
  echo "Usage: bash scripts/koradaso_termux_local.sh [--crawl]" >&2
  exit 2
fi

# The runtime route and free port must both be real before starting Flask.
python - "$PORT" <<'PY'
import socket
import sys
from app import app

port = int(sys.argv[1])
routes = {rule.rule for rule in app.url_map.iter_rules()}
required = {"/koradaso", "/world", "/search", "/koradaso/web-search", "/arena"}
missing = sorted(required - routes)
if missing:
    raise SystemExit("KORADASO refused: missing routes " + ", ".join(missing))
with socket.socket() as sock:
    try:
        sock.bind(("127.0.0.1", port))
    except OSError:
        raise SystemExit(f"KORADASO refused: port {port} is already occupied; existing server untouched.")
print(f"KORADASO routes registered; starting isolated loopback server on 127.0.0.1:{port}", flush=True)
PY

# Seed the phone's default index once from reviewed public metadata.
# An explicitly configured index always takes priority.
if [[ -z "${OAP_KORADASO_WEB_INDEX:-}" ]]; then
  export OAP_KORADASO_WEB_INDEX="$index_path"
  if [[ ! -e "$OAP_KORADASO_WEB_INDEX" ]]; then
    (
      mkdir -p -- "$index_dir" || exit 1
      index_tmp="$(mktemp "$index_dir/.public-index.XXXXXX")" || exit 1
      trap 'rm -f -- "$index_tmp"' EXIT
      python scripts/koradaso_index_public.py --source scripts/koradaso_starter_pages.jsonl --db "$index_tmp" || exit 1
      # Publish the complete database without replacing an index created by a concurrent launch.
      ln -T -- "$index_tmp" "$OAP_KORADASO_WEB_INDEX" || [[ -f "$OAP_KORADASO_WEB_INDEX" ]]
    ) || printf '%s\n' "KORADASO starter index unavailable. OAP Catalogue remains available." >&2
  fi
fi

# Open the real route only after an actual HTTP 200 response with KORADASO branding.
# The browser remains optional; HEAD-only 200 checks are insufficient.
if [[ "${OAP_KORADASO_OPEN_BROWSER:-1}" == "1" ]] && command -v termux-open-url >/dev/null 2>&1; then
  (
    for attempt in 1 2 3 4 5 6 7 8 9 10; do
      page="$(curl --noproxy '*' -fsS --max-time 2 "http://127.0.0.1:$PORT/koradaso" 2>/dev/null || true)"
      if [[ "$page" == *'KORADASO Internet · ON ANY POSTCODE'* && "$page" == *'id="address-form"'* ]]; then
        termux-open-url "http://127.0.0.1:$PORT/koradaso" >/dev/null 2>&1 || true
        exit 0
      fi
      sleep 1
    done
    echo "KORADASO browser not opened: live branded /koradaso page not verified." >&2
  ) &
fi

exec python -m flask --app app run --host 127.0.0.1 --port "$PORT" --no-debugger --no-reload
