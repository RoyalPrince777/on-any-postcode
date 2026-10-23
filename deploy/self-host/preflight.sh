#!/usr/bin/env bash
# Read-only preflight for an OAP-owned Linux host. Does not deploy or modify firewall/DNS.
set -u
fail=0
check() { if "$@" >/dev/null 2>&1; then printf 'PASS %s\n' "$*"; else printf 'FAIL %s\n' "$*"; fail=1; fi; }
printf 'OAP self-host preflight (local checks only)\n'
check uname -s
check docker --version
check docker compose version
check git --version
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  echo 'PASS Docker daemon reachable'
else
  echo 'FAIL Docker daemon not reachable'; fail=1
fi
if [ -f deploy/self-host/.env ]; then
  echo 'PASS local env file exists (contents not printed)'
  check docker compose -f deploy/self-host/compose.yaml --env-file deploy/self-host/.env config --quiet
else
  echo 'NOT READY deploy/self-host/.env absent; do not add secrets to Git'
  fail=1
fi
if command -v ss >/dev/null 2>&1; then
  echo 'Local listeners on 80/443 (review before gateway startup):'
  ss -ltn '( sport = :80 or sport = :443 )' || true
fi
printf '\nExternal checks still required: public IPv4/CGNAT, router forwarding, DNS, TLS, PostgreSQL migrations, backups, TURN, two-phone test.\n'
exit "$fail"
