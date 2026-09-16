FROM ghcr.io/project-osrm/osrm-backend:v6.0.0

USER root

ARG OAP_ROUTING_PBF_URL=https://download.geofabrik.de/europe/united-kingdom/england/greater-london-latest.osm.pbf
ENV OAP_ROUTING_DATA_DIR=/data

COPY routing/bootstrap.sh /usr/local/bin/oap-routing-bootstrap
RUN chmod 0755 /usr/local/bin/oap-routing-bootstrap \
    && mkdir -p /data \
    && case "$OAP_ROUTING_PBF_URL" in https://*) ;; *) echo "OAP Routing: refusing non-HTTPS build source" >&2; exit 64 ;; esac \
    && wget -q -O /data/greater-london.osm.pbf "$OAP_ROUTING_PBF_URL" \
    && osrm-extract -p /opt/car.lua /data/greater-london.osm.pbf \
    && STEM=/data/greater-london \
    && for f in "$STEM".osrm*; do suffix="${f#$STEM}"; mv "$f" "/data/oap$suffix"; done \
    && osrm-partition /data/oap.osrm \
    && osrm-customize /data/oap.osrm \
    && rm -f /data/greater-london.osm.pbf

# Render web startup now only launches the already-built OAP-controlled graph.
# No public/demo route-computation fallback.
EXPOSE 10000
ENTRYPOINT ["/usr/local/bin/oap-routing-bootstrap"]
