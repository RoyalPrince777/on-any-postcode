#!/bin/sh
set -eu

DATA_DIR="${OAP_ROUTING_DATA_DIR:-/data}"
PBF="$DATA_DIR/greater-london.osm.pbf"
BASE="$DATA_DIR/oap"
PROFILE="/opt/car.lua"


mkdir -p "$DATA_DIR"

# Build the OAP-controlled graph only when it is absent. The downloaded OSM
# extract is source data; all route computation is performed by this service.
if [ ! -f "$BASE.osrm.partition" ] || [ ! -f "$BASE.osrm.cells" ]; then
  echo "OAP Routing: preparing Greater London road graph"
  if [ ! -s "$PBF" ]; then
    echo "OAP Routing: missing prepared road extract at $PBF" >&2
    exit 65
  fi
  rm -f "$BASE".osrm*
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
exec osrm-routed --algorithm mld --ip 0.0.0.0 --port "${PORT:-10000}" "$BASE.osrm"
