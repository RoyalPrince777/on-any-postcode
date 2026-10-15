#!/bin/sh
set -eu
URL="${OAP_ROUTING_PBF_URL:-https://download.geofabrik.de/europe/united-kingdom/england/greater-london-latest.osm.pbf}"
DEST=/data/greater-london.osm.pbf
TMP="${DEST}.tmp"
case "$URL" in
  https://*) ;;
  *) echo "OAP Routing: road data source must use HTTPS" >&2; exit 64 ;;
esac
mkdir -p /data
if [ -s "$DEST" ]; then
  echo "OAP Routing: existing nonempty road extract retained"
  exit 0
fi
trap 'rm -f "$TMP"' EXIT HUP INT TERM
rm -f "$TMP"
curl --fail --show-error --silent --location \
  --proto '=https' --proto-redir '=https' \
  --retry 3 --connect-timeout 30 --max-time 1800 \
  --output "$TMP" "$URL"
test -s "$TMP" || { echo "OAP Routing: downloaded road extract is empty" >&2; exit 65; }
mv "$TMP" "$DEST"
trap - EXIT HUP INT TERM
echo "OAP Routing: HTTPS road extract prepared"
