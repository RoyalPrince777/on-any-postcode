FROM ghcr.io/project-osrm/osrm-backend:v6.0.0

USER root

ARG OAP_ROUTING_PBF_URL=https://download.geofabrik.de/europe/united-kingdom/england/east-sussex-latest.osm.pbf

RUN mkdir -p /data \
    && case "$OAP_ROUTING_PBF_URL" in https://*) ;; *) echo "OAP Routing: refusing non-HTTPS build source" >&2; exit 64 ;; esac \
    && wget -q -O /data/region.osm.pbf "$OAP_ROUTING_PBF_URL" \
    && osrm-extract -p /opt/car.lua /data/region.osm.pbf \
    && STEM=/data/region \
    && for f in "$STEM".osrm*; do suffix="${f#$STEM}"; mv "$f" "/data/oap$suffix"; done \
    && osrm-partition /data/oap.osrm \
    && osrm-customize /data/oap.osrm \
    && rm -f /data/region.osm.pbf

EXPOSE 10000
ENTRYPOINT ["sh", "-c", "exec osrm-routed --algorithm mld --ip 0.0.0.0 --port ${PORT:-10000} /data/oap.osrm"]
