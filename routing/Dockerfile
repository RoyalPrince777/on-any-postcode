FROM ghcr.io/project-osrm/osrm-backend:v5.27.1

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends wget ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY routing/bootstrap.sh /usr/local/bin/oap-routing-bootstrap
RUN chmod 0755 /usr/local/bin/oap-routing-bootstrap

# Route computation remains inside this OAP-controlled service. There is no
# public/demo OSRM runtime fallback.
EXPOSE 10000
ENTRYPOINT ["/usr/local/bin/oap-routing-bootstrap"]
