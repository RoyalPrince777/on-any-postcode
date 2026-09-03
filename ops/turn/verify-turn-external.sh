#!/usr/bin/env bash
set -euo pipefail

required=(OAP_TURN_HOST OAP_TURN_SHARED_SECRET)
for name in "${required[@]}"; do
  if [[ -z "${!name:-}" ]]; then
    echo "missing verification setting: ${name}" >&2
    exit 64
  fi
done

if [[ "${OAP_TURN_EXTERNAL_PROBE:-}" != "true" ]]; then
  echo "refusing local/ambiguous probe: set OAP_TURN_EXTERNAL_PROBE=true only on a separate external network" >&2
  exit 64
fi
if [[ ! "$OAP_TURN_HOST" =~ ^[A-Za-z0-9.-]{3,253}$ ]]; then
  echo "invalid OAP_TURN_HOST" >&2
  exit 64
fi
if [[ ! "$OAP_TURN_SHARED_SECRET" =~ ^[A-Za-z0-9_-]{32,128}$ ]]; then
  echo "invalid OAP_TURN_SHARED_SECRET" >&2
  exit 64
fi

for command in turnutils_uclient openssl getent timeout; do
  command -v "$command" >/dev/null 2>&1 || {
    echo "required verification command is missing: $command" >&2
    exit 69
  }
done

turn_ip="$(getent ahostsv4 "$OAP_TURN_HOST" | awk 'NR==1 {print $1}')"
if [[ -z "$turn_ip" ]]; then
  echo "TURN hostname did not resolve to IPv4" >&2
  exit 69
fi

probe_user="oap-relay-proof"
run_probe() {
  local label="$1"
  shift
  echo "running ${label} relay proof" >&2
  timeout 30s turnutils_uclient -y -X -c -n 3 -u "$probe_user" -W "$OAP_TURN_SHARED_SECRET" "$@" "$turn_ip" >/dev/null
}

run_probe "UDP" -p 3478
run_probe "TCP" -t -p 3478

# Verify the public TLS certificate with hostname validation before the TURN/TLS data path.
timeout 20s openssl s_client \
  -connect "${OAP_TURN_HOST}:5349" \
  -servername "$OAP_TURN_HOST" \
  -verify_hostname "$OAP_TURN_HOST" \
  -verify_return_error \
  </dev/null >/dev/null 2>&1
run_probe "TLS" -t -S -p 5349

printf '%s\n' 'OAP_TURN_EXTERNAL_RELAY_PROOF_V1_PASS'
