#!/data/data/com.termux/files/usr/bin/bash
# Read-only evidence for the EXISTING KORADASO server on port 5052.
# No git pull/reset, no imports of app.py, no restarts, installs, or file writes.
set -u
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$ROOT" || ! -f "$ROOT/app.py" ]]; then
  echo 'KORADASO CHECK: run from the existing on-any-postcode checkout.' >&2
  exit 2
fi
cd "$ROOT" || exit 2
echo '=== KORADASO 5052 · READ-ONLY EVIDENCE ==='
printf 'Directory: %s\n' "$ROOT"
printf 'Git head: '; git rev-parse --short HEAD 2>/dev/null || echo unknown
printf 'Git branch: '; git branch --show-current 2>/dev/null || echo unknown
printf 'Tracked changes: '; git diff --name-only 2>/dev/null | wc -l
printf 'Untracked paths: '; git ls-files --others --exclude-standard 2>/dev/null | wc -l
echo 'Local route implementation (source inspection only):'
python - <<'PY'
import ast
from pathlib import Path
files = (
    ('KORADASO homepage', 'app.py', '/koradaso'),
    ('OAP catalogue', 'mission_control/oap_store.py', '/search'),
    ('WWW Search', 'mission_control/oap_store.py', '/koradaso/web-search'),
    ('SMI public Studio', 'app.py', '/studio'),
    ('SMI public chat', 'app.py', '/studio/chat'),
)
for label, name, route in files:
    p=Path(name)
    if not p.is_file():
        print(f'{label}: UNKNOWN — module missing')
        continue
    try:
        node=ast.parse(p.read_text(encoding='utf-8'))
        exists=any(
            isinstance(fn,(ast.FunctionDef,ast.AsyncFunctionDef))
            and any(isinstance(d,ast.Call) and d.args and isinstance(d.args[0],ast.Constant)
                    and d.args[0].value==route for d in fn.decorator_list)
            for fn in ast.walk(node)
        )
        print(f'{label}: {"SOURCE PRESENT" if exists else "SOURCE MISSING"}')
    except (SyntaxError,UnicodeError,OSError):
        print(f'{label}: UNKNOWN — cannot parse safely')
print('First-party index module:', 'SOURCE PRESENT' if Path('mission_control/koradaso_web_index.py').is_file() else 'SOURCE MISSING')
print('Royal homepage template:', 'SOURCE PRESENT' if Path('templates/koradaso_internet.html').is_file() else 'SOURCE MISSING')
print('SMI Studio template:', 'SOURCE PRESENT' if Path('templates/studio_public.html').is_file() else 'SOURCE MISSING')
print('Original KORADASO logo:', 'SOURCE PRESENT' if Path('static/oap/koradaso_internet_logo.jpg').is_file() else 'SOURCE MISSING')
PY
echo 'Actual localhost 5052 HTTP results (no credentials or cookies):'
for target in '/koradaso' '/search?q=koradaso' '/koradaso/web-search?q=koradaso' '/studio?source=koradaso' '/arena' '/world'; do
  printf '%s => ' "$target"
  curl --noproxy '*' -sS --max-time 8 -o /dev/null -w 'HTTP %{http_code} · %{time_total}s\n' "http://127.0.0.1:5052$target" 2>&1 || echo 'NOT REACHABLE'
done
echo 'Private Founder boundary (no credentials, no redirect follow):'
printf '/mission/smi => '
curl --noproxy '*' -sS --max-time 8 -o /dev/null -w 'HTTP %{http_code}\n' 'http://127.0.0.1:5052/mission/smi' 2>&1 || echo 'NOT REACHABLE'
echo 'NOTE: Redirect or denial is not comprehensive access-control proof.'
echo 'READ-ONLY CHECK COMPLETE. No code, sessions or server process changed.'
