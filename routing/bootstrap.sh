#!/bin/sh
set -eu

DATA_DIR="${OAP_ROUTING_DATA_DIR:-/data}"
PBF_URL="${OAP_ROUTING_PBF_URL:-https://download.geofabrik.de/europe/united-kingdom/england/greater-london-latest.osm.pbf}"
PBF="$DATA_DIR/greater-london.osm.pbf"
BASE="$DATA_DIR/oap"
PROFILE="/opt/car.lua"

mkdir -p "$DATA_DIR"

# Build the OAP-controlled graph only when it is absent. The downloaded OSM
# extract is source data; all route computation is performed by this service.
if [ ! -f "$BASE.osrm.partition" ] || [ ! -f "$BASE.osrm.cells" ]; then
  echo "OAP Routing: preparing Greater London road graph"
  rm -f "$BASE".osrm* "$PBF.tmp"
  wget -q --https-only -O "$PBF.tmp" "$PBF_URL"
  mv "$PBF.tmp" "$PBF"
  osrm-extract -p "$PROFILE" "$PBF"
  # osrm-extract names output from the PBF stem; normalize it to /data/oap.*
  STEM="${PBF%.osm.pbf}"
  for f in "$STEM".osrm*; do
    suffix="${f#$STEM}"
    mv "$f" "$BASE$suffix"
  done
  osrm-partition "$BASE.osrm"
  osrm-customize "$BASE.osrm"
fi

echo "OAP Routing: starting first-party route engine"
exec osrm-routed --algorithm mld --port "${PORT:-10000}" "$BASE.osrm"
