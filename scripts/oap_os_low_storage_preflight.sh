#!/usr/bin/env bash
# OAP OS: low-storage preparation; never downloads AOSP or flashes a device.
set -Eeuo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
printf 'OAP OS low-storage preflight (no AOSP checkout)\n'
printf 'Host: '; uname -srm
printf 'Disk free on current workspace:\n'; df -h "$root"
printf 'Memory:\n'
if command -v free >/dev/null 2>&1; then free -h; else echo 'Not available'; fi
for command in git sha256sum python3; do
  if command -v "$command" >/dev/null 2>&1; then printf 'OK %s\n' "$command"; else printf 'MISSING %s\n' "$command"; fi
done
for path in \
  "$root/oap_os/aosp/vendor/oap/Android.mk" \
  "$root/oap_os/aosp/vendor/oap/oap_product.mk" \
  "$root/android/oapworld/src/main/AndroidManifest.xml"; do
  test -s "$path" || { echo "MISSING $path" >&2; exit 1; }
done
if [[ -n "${OAP_APK_PATH:-}" ]]; then
  test -s "$OAP_APK_PATH" || { echo 'APK path missing/empty' >&2; exit 1; }
  printf 'APK SHA256: '; sha256sum "$OAP_APK_PATH"
else
  echo 'APK not supplied: set OAP_APK_PATH to validate an existing build artifact.'
fi
echo 'PASS: lightweight source prerequisites. AOSP checkout, image, boot and security remain unverified.'
