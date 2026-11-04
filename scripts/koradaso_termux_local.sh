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
export OAP_SURFACE_ROLE=""
export FLASK_DEBUG=0

# The runtime route and free port must both be real before starting Flask.
python - "$PORT" <<'PY'
import socket
import sys
from app import app

port = int(sys.argv[1])
routes = {rule.rule for rule in app.url_map.iter_rules()}
required = {"/koradaso", "/world", "/search"}
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

exec python -m flask --app app run --host 127.0.0.1 --port "$PORT" --no-debugger --no-reload
