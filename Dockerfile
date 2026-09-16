FROM ghcr.io/project-osrm/osrm-backend:v6.0.0

USER root

COPY routing/bootstrap.sh /usr/local/bin/oap-routing-bootstrap
RUN chmod 0755 /usr/local/bin/oap-routing-bootstrap

# Render API-created Docker services build ./Dockerfile.
# Routing remains inside the OAP-controlled OSRM runtime; no public/demo route fallback.
EXPOSE 10000
ENTRYPOINT ["/usr/local/bin/oap-routing-bootstrap"]
