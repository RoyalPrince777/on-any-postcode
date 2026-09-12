#!/usr/bin/env sh
set -eu

BASE_URL="${1:-https://oap-smi.onrender.com}"

probe() {
  path="$1"
  printf '\n=== %s ===\n' "$path"
  curl -sS -o /dev/null -D - \
    --connect-timeout 10 \
    --max-time 20 \
    -H 'Cache-Control: no-cache' \
    -H 'Pragma: no-cache' \
    "${BASE_URL}${path}" \
  | awk 'BEGIN{IGNORECASE=1} /^HTTP\// || /^retry-after:/ || /^server:/ || /^via:/ || /^x-request-id:/ || /^cf-ray:/ || /^x-render-/ {print}'
}

# Anonymous GETs only. Never submit the Founder credential from this probe.
probe '/auth/recover-founder?next=/mission/ollama'
probe '/auth/founder-entry?next=/mission/ollama'
