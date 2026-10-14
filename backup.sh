#!/usr/bin/env bash
# Local OAP source + SQLite snapshot. NOT a production PostgreSQL/Neon Auth backup.
set -Eeuo pipefail
umask 077

root="${OAP_BACKUP_ROOT:-$HOME/oap}"
destination="${OAP_BACKUP_DEST:-$root/backups}"
[[ -d "$root" ]] || { echo "Backup failed: OAP directory missing" >&2; exit 1; }
[[ -f "$root/app.py" && -f "$root/oap.db" ]] || {
  echo "Backup failed: app.py or oap.db missing" >&2; exit 1;
}
command -v git >/dev/null || { echo "Backup failed: git missing" >&2; exit 1; }
git -C "$root" rev-parse --is-inside-work-tree >/dev/null || {
  echo "Backup failed: OAP directory is not a Git working tree" >&2; exit 1;
}
python_bin="$(command -v python3 || command -v python || true)"
[[ -n "$python_bin" ]] || { echo "Backup failed: Python missing" >&2; exit 1; }
mkdir -p -- "$destination"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
snapshot="$(mktemp -d "$destination/.oap-backup-${stamp}-XXXXXXXX")"
complete=0
cleanup() {
  if [[ "$complete" -ne 1 ]]; then
    rm -rf -- "$snapshot"
    echo "Backup failed: incomplete snapshot removed" >&2
  fi
}
trap cleanup EXIT
cp -- "$root/app.py" "$snapshot/app.py"
# SQLite's online backup API avoids a torn copy of a live database.
"$python_bin" - "$root/oap.db" "$snapshot/oap.db" <<'PY'
import sqlite3
import sys
source = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
target = sqlite3.connect(sys.argv[2])
try:
    source.backup(target)
    result = target.execute("PRAGMA integrity_check").fetchone()
    if result != ("ok",):
        raise RuntimeError("SQLite integrity check failed")
finally:
    target.close()
    source.close()
PY
git -C "$root" bundle create "$snapshot/oap-history.bundle" --all
git -C "$root" bundle verify "$snapshot/oap-history.bundle" >/dev/null
"$python_bin" - "$snapshot" <<'PY'
from hashlib import sha256
from pathlib import Path
import sys
folder = Path(sys.argv[1])
with (folder / "SHA256SUMS").open("w", encoding="utf-8") as manifest:
    for item in sorted(folder.iterdir()):
        if item.is_file():
            manifest.write(f"{sha256(item.read_bytes()).hexdigest()}  {item.name}\n")
PY
final="$destination/oap-${stamp}-$$"
mv -- "$snapshot" "$final"
complete=1
trap - EXIT
echo "Local backup complete: $final"
echo "NOT VERIFIED: off-device custody, production PostgreSQL, Neon Auth, or restore drill."
