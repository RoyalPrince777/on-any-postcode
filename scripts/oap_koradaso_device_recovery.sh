#!/usr/bin/env bash
# One bounded KORADASO local route recovery; no global package install, push, deploy or auth bypass.
set -Eeuo pipefail
repo="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo"
python - <<'PY'
from datetime import datetime
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

app_path = Path("app.py")
template = Path("templates/koradaso_internet.html")
remote_ref = "origin/feature/smi-organism-anatomy-monitor-20261103"
if not app_path.is_file() or not Path(".git").exists():
    raise SystemExit("OAP_CORE_REPO_OR_APP_MISSING")
source = app_path.read_text()
route_tag = '@app.get("/koradaso")'
route_missing = route_tag not in source

# Check all prerequisites before any mutation. Never overwrite Founder-edited templates.
if not template.is_file():
    try:
        payload = subprocess.check_output(
            ["git", "show", f"{remote_ref}:templates/koradaso_internet.html"],
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        raise SystemExit("KORADASO_TEMPLATE_MISSING: fetch the existing PR branch first")
    if b"KORADASO" not in payload or not payload.strip().startswith(b"<!doctype html>"):
        raise SystemExit("KORADASO_TEMPLATE_INVALID")
else:
    payload = None

updated = source
if route_missing:
    # Fail closed if route registration differs from the expected local application.
    marker = '@app.get("/world")'
    if source.count(marker) != 1:
        raise SystemExit("KORADASO_ROUTE_ANCHOR_NOT_UNIQUE")
    if "render_template" not in source or "make_response" not in source:
        raise SystemExit("KORADASO_FLASK_IMPORTS_UNVERIFIED")
    route = (
        '@app.get("/koradaso")\n'
        'def koradaso_internet_home():\n'
        '    """First-party local KORADASO start page; no authority granted."""\n'
        '    response = make_response(render_template("koradaso_internet.html"))\n'
        '    response.headers["Cache-Control"] = "no-store"\n'
        '    return response\n\n\n'
    )
    updated = source.replace(marker, route + marker, 1)
    compile(updated, str(app_path), "exec")

# Template creation is non-destructive; existing artwork is never overwritten.
if payload is not None:
    template.parent.mkdir(parents=True, exist_ok=True)
    with template.open("xb") as f:
        f.write(payload)
    print("KORADASO_TEMPLATE_RESTORED_FROM_EXISTING_PR")

if route_missing:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup = app_path.with_name(f"app.py.before_koradaso_{stamp}.bak")
    shutil.copy2(app_path, backup)
    fd, tmp = tempfile.mkstemp(prefix=".oap-koradaso-", dir=str(app_path.parent))
    try:
        with os.fdopen(fd, "w") as f:
            f.write(updated)
        os.chmod(tmp, app_path.stat().st_mode & 0o777)
        os.replace(tmp, app_path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    print("KORADASO_ROUTE_ADDED_WITH_LOCAL_BACKUP")
else:
    print("KORADASO_ROUTE_SOURCE_PRESENT")
print("OAP_KORADASO_SOURCE_READY")
PY

if [[ ! -x ".venv-core/bin/python" ]]; then
  echo "OAP_CORE_ENV_MISSING: source recovery completed; device runtime proof unavailable"
  exit 2
fi
# Reuse Termux's installed native cryptography/Pillow; do not install or copy packages.
system_packages="$(python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
PYTHONPATH="$system_packages" OAP_LOCAL_MODE=true OAP_SURFACE_ROLE=local \
 OAP_AUTH_REQUIRED=true FLASK_DEBUG=0 .venv-core/bin/python - <<'PY'
from app import app
with app.test_client() as client:
    expected_public = ("/world", "/koradaso")
    for route in expected_public:
        res = client.get(route, follow_redirects=False)
        print(f"OAP_DEVICE_ROUTE {route} HTTP {res.status_code}")
        if res.status_code != 200:
            raise SystemExit("OAP_DEVICE_PUBLIC_ROUTE_NOT_READY")
    res = client.get("/mission/ollama", follow_redirects=False)
    print(f"OAP_DEVICE_PRIVATE_ROUTE /mission/ollama HTTP {res.status_code}")
    if res.status_code not in (302, 303, 401, 403, 503):
        raise SystemExit("OAP_DEVICE_SMI_AUTH_BOUNDARY_UNVERIFIED")
print("OAP_KORADASO_DEVICE_ROUTE_PROOF_PASSED")
PY
