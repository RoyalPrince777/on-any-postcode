#!/data/data/com.termux/files/usr/bin/bash
# KORADASO first-party WWW route repair for an older existing Termux checkout.
# Adds only the missing blueprint route and its local index/template, preserving the live homepage.
# Does NOT restart Flask, launch crawlers, change public exposure, pull/merge/reset or install dependencies.
set -Eeuo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$ROOT" || ! -f "$ROOT/app.py" || ! -f "$ROOT/mission_control/oap_store.py" ]]; then
  echo "SAFE STOP: run from the existing on-any-postcode checkout; no files changed." >&2
  exit 2
fi
cd "$ROOT"
if [[ "$(curl --noproxy '*' -fsS -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1:5052/koradaso 2>/dev/null || true)" != "200" ]]; then
  echo "SAFE STOP: existing KORADASO 5052 must already be responding 200; no files changed." >&2
  exit 2
fi
python - <<'PY'
from app import app
routes = {rule.rule for rule in app.url_map.iter_rules()}
if '/koradaso' not in routes or '/search' not in routes:
    raise SystemExit('SAFE STOP: existing KORADASO/OAP Search routes absent.')
if '/koradaso/web-search' in routes:
    raise SystemExit('ALREADY PRESENT: WWW Search route exists; no files changed.')
PY
# Never overwrite existing local modules, including edited Founder files.
for file in mission_control/koradaso_web_index.py mission_control/templates/koradaso_web_search.html; do
  if [[ -e "$file" ]]; then
    echo "SAFE STOP: $file already exists; manual reconciliation needed; no files changed." >&2
    exit 2
  fi
done
BASE='https://raw.githubusercontent.com/RoyalPrince777/on-any-postcode/6a0441674975c5847bb699de7955c4300851816a'
STAGE="$(mktemp -d)"
trap 'rm -rf -- "$STAGE"' EXIT
mkdir -p "$STAGE/mission_control/templates"
curl -fLsS --retry 2 "$BASE/mission_control/koradaso_web_index.py" -o "$STAGE/mission_control/koradaso_web_index.py"
curl -fLsS --retry 2 "$BASE/mission_control/templates/koradaso_web_search.html" -o "$STAGE/mission_control/templates/koradaso_web_search.html"
# Verify downloaded code and inspect old blueprint. All checks precede file writes.
python - "$STAGE" <<'PY'
from pathlib import Path
import ast
import sys
stage = Path(sys.argv[1])
index = (stage/'mission_control/koradaso_web_index.py').read_text()
template = (stage/'mission_control/templates/koradaso_web_search.html').read_text()
current = Path('mission_control/oap_store.py').read_text()
ast.parse(index)
ast.parse(current)
if 'def search_public_pages(' not in index or 'def _safe_public_url(' not in index:
    raise SystemExit('SAFE STOP: downloaded search module failed integrity checks.')
if 'action="/koradaso/web-search"' not in template or 'Web index unavailable.' not in template:
    raise SystemExit('SAFE STOP: downloaded search template failed integrity checks.')
if 'bp = Blueprint("oap_store"' not in current or '@bp.get("/search")' not in current:
    raise SystemExit('SAFE STOP: expected OAP Store blueprint missing; no files changed.')
if '/koradaso/web-search' in current:
    raise SystemExit('SAFE STOP: route source already exists but was not registered; inspect registration.')
PY
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/.koradaso-refresh-backups/search_route_$STAMP"
mkdir -p "$BACKUP/mission_control"
cp -p mission_control/oap_store.py "$BACKUP/mission_control/oap_store.py"
rollback() {
  cp -p "$BACKUP/mission_control/oap_store.py" mission_control/oap_store.py
  rm -f mission_control/koradaso_web_index.py mission_control/templates/koradaso_web_search.html
  echo "SAFE ROLLBACK: original OAP Store restored; new files removed." >&2
}
cp -- "$STAGE/mission_control/koradaso_web_index.py" mission_control/koradaso_web_index.py
cp -- "$STAGE/mission_control/templates/koradaso_web_search.html" mission_control/templates/koradaso_web_search.html
cat >> mission_control/oap_store.py <<'PY'

# KORADASO first-party WWW Search compatibility route.
# No crawler, third-party provider or background job is started here.
@bp.get("/koradaso/web-search")
def koradaso_public_web_search():
    from flask import make_response as _make_response
    from flask import render_template as _render_template
    from flask import request as _request
    from . import koradaso_web_index as _index
    query = str(_request.args.get("q") or "").strip()[:120]
    results, index_ready = _index.search_public_pages(query)
    response = _make_response(_render_template(
        "koradaso_web_search.html",
        query=query, results=results, index_ready=index_ready,
    ), 200 if index_ready else 503)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Robots-Tag"] = "noindex, noarchive"
    return response
PY
if ! python - <<'PY'
import ast
from pathlib import Path
from app import app
for f in ['mission_control/oap_store.py','mission_control/koradaso_web_index.py']:
    ast.parse(Path(f).read_text())
routes={rule.rule for rule in app.url_map.iter_rules()}
assert '/koradaso/web-search' in routes, 'missing installed route'
client=app.test_client()
response=client.get('/koradaso/web-search?q=termux')
assert response.status_code in {200,503}, f'unexpected response {response.status_code}'
assert b'KORADASO' in response.data, 'unrecognised search template'
print(f'KORADASO compatibility verified: route returns HTTP {response.status_code} in Flask test client.')
PY
then
  rollback
  exit 2
fi
echo "KORADASO first-party route source repaired. Backup: $BACKUP"
echo "EXISTING homepage untouched; WWW Search is NOT claimed ready or publicly approved."
echo "Existing 5052 Flask process must be restarted once to load the route; no restart performed."
echo "When restarted, verify /koradaso/web-search?q=test locally. HTTP 503 means index unavailable, not a successful search."
