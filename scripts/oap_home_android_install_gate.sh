#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

APK="${1:-$HOME/storage/downloads/OAPHome777/OAPHome-debug.apk}"
V2="com.onanypostcode.oaphome.v2"
V1="com.onanypostcode.oaphome"

echo "OAP_HOME_INSTALL_GATE_START"

[[ -s "${APK}" ]] || {
  echo "APK_MISSING:${APK}"
  exit 1
}

echo "APK_PATH=${APK}"
echo "APK_SHA256=$(sha256sum "${APK}" | awk '{print $1}')"

V2_PATH="$(pm path "${V2}" 2>/dev/null || true)"
V1_PATH="$(pm path "${V1}" 2>/dev/null || true)"

if [[ -n "${V2_PATH}" ]]; then
  echo "V2_INSTALLED=YES"
  echo "V2_PATH=${V2_PATH}"
else
  echo "V2_INSTALLED=NO"
fi

if [[ -n "${V1_PATH}" ]]; then
  echo "V1_INSTALLED=YES"
  echo "V1_PATH=${V1_PATH}"
else
  echo "V1_INSTALLED=NO"
fi

APPOPS="$(cmd appops get com.termux REQUEST_INSTALL_PACKAGES 2>/dev/null || true)"
if [[ -n "${APPOPS}" ]]; then
  echo "TERMUX_INSTALL_APPOPS=${APPOPS//$'\n'/ }"
else
  echo "TERMUX_INSTALL_APPOPS=UNKNOWN"
fi

if [[ -n "${V2_PATH}" ]]; then
  echo "RESULT=EXISTING_V2_PRESENT"
  echo "NEXT=VERIFY_EXISTING_V2_SIGNATURE_BEFORE_ANY_UNINSTALL"
  exit 2
fi

echo "RESULT=NO_EXISTING_V2"
echo "NEXT=OPEN_UNKNOWN_APP_PERMISSION_THEN_RETRY_INSTALL"

am start \
  -a android.settings.MANAGE_UNKNOWN_APP_SOURCES \
  -d package:com.termux >/dev/null 2>&1 || true

echo "OAP_HOME_INSTALL_GATE_COMPLETE"
