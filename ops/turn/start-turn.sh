#!/usr/bin/env bash
set -euo pipefail

required=(
  OAP_TURN_REALM
  OAP_TURN_EXTERNAL_IP
  OAP_TURN_SHARED_SECRET
  OAP_TURN_CERT
  OAP_TURN_PKEY
)
for name in "${required[@]}"; do
  if [[ -z "${!name:-}" ]]; then
    echo "missing required TURN setting: ${name}" >&2
    exit 64
  fi
  if [[ "${!name}" == *$'\n'* || "${!name}" == *$'\r'* ]]; then
    echo "invalid newline in TURN setting: ${name}" >&2
    exit 64
  fi
done

if [[ ! "$OAP_TURN_REALM" =~ ^[A-Za-z0-9.-]{3,253}$ ]]; then
  echo "invalid OAP_TURN_REALM" >&2
  exit 64
fi
if [[ ! "$OAP_TURN_EXTERNAL_IP" =~ ^[0-9]{1,3}(\.[0-9]{1,3}){3}$ ]]; then
  echo "OAP_TURN_EXTERNAL_IP must be a public IPv4 address for v1" >&2
  exit 64
fi
if [[ ! "$OAP_TURN_SHARED_SECRET" =~ ^[A-Za-z0-9_-]{32,128}$ ]]; then
  echo "OAP_TURN_SHARED_SECRET must be 32-128 base64url-safe characters" >&2
  exit 64
fi
if [[ "$OAP_TURN_CERT" != /* || "$OAP_TURN_PKEY" != /* ]]; then
  echo "TURN certificate paths must be absolute" >&2
  exit 64
fi
if [[ ! -r "$OAP_TURN_CERT" || ! -r "$OAP_TURN_PKEY" ]]; then
  echo "TURN certificate or private key is not readable" >&2
  exit 66
fi

runtime_dir=/run/oap-turn
config_file="$runtime_dir/turnserver.conf"
mkdir -p "$runtime_dir"
umask 077

cat >"$config_file" <<EOF
listening-port=3478
tls-listening-port=5349
fingerprint
use-auth-secret
static-auth-secret=$OAP_TURN_SHARED_SECRET
realm=$OAP_TURN_REALM
server-name=$OAP_TURN_REALM
external-ip=$OAP_TURN_EXTERNAL_IP
cert=$OAP_TURN_CERT
pkey=$OAP_TURN_PKEY
min-port=49152
max-port=49252
stale-nonce=600
allocation-default-address-family=ipv4
user-quota=8
total-quota=1000
no-multicast-peers
no-software-attribute
syslog

denied-peer-ip=0.0.0.0-0.255.255.255
denied-peer-ip=10.0.0.0-10.255.255.255
denied-peer-ip=100.64.0.0-100.127.255.255
denied-peer-ip=127.0.0.0-127.255.255.255
denied-peer-ip=169.254.0.0-169.254.255.255
denied-peer-ip=172.16.0.0-172.31.255.255
denied-peer-ip=192.0.0.0-192.0.0.255
denied-peer-ip=192.0.2.0-192.0.2.255
denied-peer-ip=192.88.99.0-192.88.99.255
denied-peer-ip=192.168.0.0-192.168.255.255
denied-peer-ip=198.18.0.0-198.19.255.255
denied-peer-ip=198.51.100.0-198.51.100.255
denied-peer-ip=203.0.113.0-203.0.113.255
denied-peer-ip=224.0.0.0-255.255.255.255
EOF

exec /usr/bin/turnserver -c "$config_file"
