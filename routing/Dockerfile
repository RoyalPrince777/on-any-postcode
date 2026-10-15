FROM ghcr.io/project-osrm/osrm-backend:v5.27.1

USER root
# Use existing base-image utilities only when they are actually present.
# Avoid stale Debian Bullseye package indexes and fail the build if HTTPS
# download prerequisites are unavailable. Do not silently downgrade TLS.
RUN command -v wget >/dev/null \
    && test -s /etc/ssl/certs/ca-certificates.crt


COPY routing/bootstrap.sh /usr/local/bin/oap-routing-bootstrap
RUN chmod 0755 /usr/local/bin/oap-routing-bootstrap

# Route computation remains inside this OAP-controlled service. There is no
# public/demo OSRM runtime fallback.
EXPOSE 10000
ENTRYPOINT ["/usr/local/bin/oap-routing-bootstrap"]
