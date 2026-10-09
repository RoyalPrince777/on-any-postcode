#!/usr/bin/env bash
# OAP OS AOSP checkout and baseline build — dedicated Linux host only.
set -Eeuo pipefail
: "${OAP_AOSP_MANIFEST_URL:=https://android.googlesource.com/platform/manifest}"
: "${OAP_AOSP_REF:?Set OAP_AOSP_REF to an explicitly reviewed, supported AOSP tag}"
: "${OAP_AOSP_DIR:?Set OAP_AOSP_DIR to a dedicated empty checkout directory}"
: "${OAP_LUNCH_TARGET:?Set OAP_LUNCH_TARGET to a target supported by this AOSP tag}"
: "${OAP_BUILD_JOBS:=4}"
case "$OAP_AOSP_DIR" in /*) ;; *) echo "OAP_AOSP_DIR must be absolute" >&2; exit 2;; esac
command -v repo >/dev/null || { echo "Missing Android repo tool" >&2; exit 2; }
command -v git >/dev/null || { echo "Missing git" >&2; exit 2; }
if [[ -e "$OAP_AOSP_DIR/.repo" ]]; then
  echo "Existing checkout detected; refusing to alter it automatically" >&2
  exit 2
fi
if [[ -d "$OAP_AOSP_DIR" && -n "$(ls -A "$OAP_AOSP_DIR")" ]]; then
  echo "Checkout destination is not empty" >&2
  exit 2
fi
mkdir -p "$OAP_AOSP_DIR"
cd "$OAP_AOSP_DIR"
repo init -u "$OAP_AOSP_MANIFEST_URL" -b "$OAP_AOSP_REF"
repo sync -c -j "$OAP_BUILD_JOBS" --fail-fast
mkdir -p out/oap-evidence
{
  printf 'aosp_ref=%s\n' "$OAP_AOSP_REF"
  printf 'lunch_target=%s\n' "$OAP_LUNCH_TARGET"
  printf 'host=%s\n' "$(uname -a)"
  git --version
  repo version
  repo manifest -r
} > out/oap-evidence/source-receipt.txt
# Use a fresh shell for the target's documented build environment.
set +u
source build/envsetup.sh
lunch "$OAP_LUNCH_TARGET"
m -j "$OAP_BUILD_JOBS" 2>&1 | tee out/oap-evidence/baseline-build.log
set -u
printf 'Build finished. Verify image outputs and emulator boot separately.\n'
