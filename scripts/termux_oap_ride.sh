#!/data/data/com.termux/files/usr/bin/bash
# Open the existing first-party OAP Ride passenger or driver web app on Android.
# Does not start a dispatch server, install an APK or handle secrets.
set -Eeuo pipefail

mode="${1:-rider}"
case "$mode" in
  rider) path="/transport/ride/rider" ;;
  driver) path="/transport/ride/driver" ;;
  current) path="/transport/ride/current" ;;
  install) path="/transport" ;;
  *)
    printf 'Usage: bash scripts/termux_oap_ride.sh [rider|driver|current|install]\n' >&2
    exit 2
    ;;
esac

origin="${OAP_RIDE_ORIGIN:-https://onanypostcode.global}"
origin="${origin%/}"
# Never launch arbitrary or clear-text hosts through an OAP-branded shortcut.
case "$origin" in
  https://onanypostcode.global|https://www.onanypostcode.global) ;;
  *)
    printf 'OAP Ride requires its approved HTTPS first-party origin.\n' >&2
    exit 2
    ;;
esac

url="$origin$path"
if ! command -v curl >/dev/null 2>&1; then
  printf 'Install curl first: pkg install curl\n' >&2
  exit 2
fi

# Check the actual hosted page before opening it; no false local/live claim.
if ! curl --fail --silent --show-error --location --max-time 12 --output /dev/null \
    --write-out '%{http_code}' "$url" | grep -qx '200'; then
  printf 'OAP Ride is not reachable at %s; the service must be deployed first.\n' "$url" >&2
  exit 1
fi

if command -v termux-open-url >/dev/null 2>&1; then
  termux-open-url "$url"
elif command -v am >/dev/null 2>&1; then
  am start -a android.intent.action.VIEW -d "$url" >/dev/null
else
  printf 'No Android URL launcher found. Open this URL in Chrome: %s\n' "$url"
  exit 1
fi
printf 'OAP Ride page launched: %s\n' "$url"
printf 'This is a web app entry, not proof of live dispatch or payment.\n'
