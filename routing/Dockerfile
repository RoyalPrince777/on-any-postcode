FROM ghcr.io/project-osrm/osrm-backend:v5.27.1

# Road-data acquisition is performed by a separate TLS-verified init service.
# This OSRM image only preprocesses and serves an already acquired local PBF.
USER root
COPY routing/bootstrap.sh /usr/local/bin/oap-routing-bootstrap
RUN chmod 0755 /usr/local/bin/oap-routing-bootstrap

EXPOSE 10000
ENTRYPOINT ["/usr/local/bin/oap-routing-bootstrap"]
