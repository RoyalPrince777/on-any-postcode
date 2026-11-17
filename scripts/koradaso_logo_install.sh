#!/usr/bin/env bash
# Install the Founder-supplied original KORADASO JPEG into the existing Flask static path.
# No resizing, recompression, remote download, secrets, route changes or deploy.
set -Eeuo pipefail
if (( $# != 1 )); then
  echo "Usage: bash scripts/koradaso_logo_install.sh /path/to/original-koradaso-logo.jpg" >&2
  exit 2
fi
src="$1"
if [[ ! -f "$src" || -L "$src" || ! -r "$src" ]]; then
  echo "KORADASO_LOGO_SOURCE_INVALID" >&2
  exit 2
fi
repo="$(cd "$(dirname "$0")/.." && pwd)"
[[ -d "$repo/.git" ]] || { echo "KORADASO_REPO_MISSING" >&2; exit 2; }
dest="$repo/static/oap/koradaso_internet_logo.jpg"
# Confirm JPEG magic and enforce a reasonable size without third-party libraries.
python - "$src" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
size = p.stat().st_size
with p.open("rb") as stream:
    header = stream.read(3)
if not 1024 <= size <= 10 * 1024 * 1024 or header != b"\xff\xd8\xff":
    raise SystemExit("KORADASO_LOGO_NOT_JPEG")
PY
mkdir -p "$(dirname "$dest")"
if [[ -e "$dest" || -L "$dest" ]]; then
  if [[ ! -L "$dest" ]] && cmp -s "$src" "$dest"; then
    echo "KORADASO_LOGO_ALREADY_INSTALLED"
    exit 0
  fi
  echo "KORADASO_LOGO_CONFLICT: refusing to replace an existing different asset" >&2
  exit 2
fi
tmp="$(mktemp "$repo/static/oap/.koradaso-logo.XXXXXXXX")"
trap 'rm -f "$tmp"' EXIT
cp -- "$src" "$tmp"
cmp -s "$src" "$tmp" || { echo "KORADASO_LOGO_COPY_MISMATCH" >&2; exit 2; }
chmod 644 "$tmp"
mv -n -- "$tmp" "$dest"
[[ -f "$dest" ]] && cmp -s "$src" "$dest" || {
  echo "KORADASO_LOGO_INSTALL_NOT_VERIFIED" >&2
  exit 2
}
echo "KORADASO_LOGO_INSTALLED_EXACT_BYTES"
echo "Location: static/oap/koradaso_internet_logo.jpg"
echo "The image is installed locally only; it has not been committed to GitHub or deployed."
