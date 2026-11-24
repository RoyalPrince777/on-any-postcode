#!/data/data/com.termux/files/usr/bin/bash
# In-place refresh of an existing KORADASO checkout. Never installs or starts another server.
set -Eeuo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$ROOT" || ! -f "$ROOT/app.py" || ! -f "$ROOT/templates/koradaso_internet.html" ]]; then
  printf '%s\n' 'KORADASO refresh stopped: run from your existing on-any-postcode project directory.' >&2
  exit 2
fi
cd "$ROOT"
if [[ "$(curl --noproxy '*' -fsS -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1:5052/koradaso 2>/dev/null || true)" != "200" ]]; then
  echo 'KORADASO refresh stopped: current localhost:5052/koradaso is not responding 200; nothing changed.' >&2
  exit 2
fi
# Check compatibility before downloading or touching any tracked file.
python - <<'PY'
from app import app
routes = {rule.rule for rule in app.url_map.iter_rules()}
needed = {"/koradaso", "/search", "/koradaso/web-search", "/studio", "/arena", "/oap-map", "/the-link"}
missing = sorted(needed-routes)
if missing:
    raise SystemExit("SAFE STOP: this running checkout lacks newer KORADASO routes: "
                     + ", ".join(missing) +
                     ". Do not replace the template alone; keep your working browser.")
PY
BASE='https://raw.githubusercontent.com/RoyalPrince777/on-any-postcode/084232dca39f3309cce29014680bfb5e3a30679b'
STAGE="$(mktemp -d)"
trap 'rm -rf -- "$STAGE"' EXIT
mkdir -p "$STAGE/static/oap"
curl -fsSL --retry 2 "$BASE/templates/koradaso_internet.html" -o "$STAGE/koradaso_internet.html"
curl -fsSL --retry 2 "$BASE/static/oap/koradaso_internet_logo.jpg" -o "$STAGE/static/oap/koradaso_internet_logo.jpg"
curl -fsSL --retry 2 "$BASE/static/koradaso_auto_update.js" -o "$STAGE/koradaso_auto_update.js"
python - "$STAGE" <<'PY'
from pathlib import Path
import sys
stage=Path(sys.argv[1])
page=(stage/"koradaso_internet.html").read_text(encoding="utf-8")
for needed in ('id="address-form"', 'id="browser-settings"', 'href="/studio?source=koradaso"', 'href="/arena"'):
    if needed not in page: raise SystemExit("SAFE STOP: downloaded KORADASO page failed integrity check: "+needed)
logo=(stage/"static/oap/koradaso_internet_logo.jpg").read_bytes()
if len(logo)<4096 or not logo.startswith(bytes((255,216,255))):
    raise SystemExit("SAFE STOP: downloaded original logo invalid")
js=(stage/"koradaso_auto_update.js").read_text(encoding="utf-8")
if len(js)<200: raise SystemExit("SAFE STOP: browser updater invalid")
PY
# Backup exact originals before replacing any file. No git reset, pull, clean or overwrite of unrelated work.
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/.koradaso-refresh-backups/$STAMP"
mkdir -p "$BACKUP/static/oap"
for p in templates/koradaso_internet.html static/oap/koradaso_internet_logo.jpg static/koradaso_auto_update.js; do
  if [[ -f "$p" ]]; then
    mkdir -p "$BACKUP/$(dirname "$p")"
    cp -p -- "$p" "$BACKUP/$p"
  fi
done
mkdir -p static/oap
cp -- "$STAGE/koradaso_internet.html" templates/koradaso_internet.html
cp -- "$STAGE/static/oap/koradaso_internet_logo.jpg" static/oap/koradaso_internet_logo.jpg
cp -- "$STAGE/koradaso_auto_update.js" static/koradaso_auto_update.js
echo "KORADASO source refreshed in place. Original files backed up: $BACKUP"
echo 'Now restart your EXISTING 5052 Flask process once, then reload http://127.0.0.1:5052/koradaso.'
echo 'No other process was started or stopped. No public release or Founder SMI access changed.'
