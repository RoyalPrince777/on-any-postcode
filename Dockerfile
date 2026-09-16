FROM ghcr.io/project-osrm/osrm-backend:v5.27.1

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends wget ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY routing/bootstrap.sh /usr/local/bin/oap-routing-bootstrap
RUN chmod 0755 /usr/local/bin/oap-routing-bootstrap

# Root entrypoint exists for Render services created through the API, which
# currently default Docker services to ./Dockerfile. Routing remains entirely
# inside the OAP-controlled OSRM runtime; there is no public/demo route fallback.
EXPOSE 10000
ENTRYPOINT ["/usr/local/bin/oap-routing-bootstrap"]
