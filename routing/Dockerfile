FROM ghcr.io/project-osrm/osrm-backend:v5.27.1

USER root
# Use existing base-image utilities only when they are actually present.
# Avoid stale Debian Bullseye package indexes and fail the build if HTTPS
# download prerequisites are unavailable. Do not silently downgrade TLS.
RUN set -eu; \
    echo 'OAP OSRM prerequisite diagnostics'; \
    for tool in sh wget curl busybox osrm-extract osrm-routed; do \
      if command -v "$tool" >/dev/null 2>&1; then \
        echo "PRESENT: $tool"; \
      else \
        echo "MISSING: $tool"; \
      fi; \
    done; \
    if test -s /etc/ssl/certs/ca-certificates.crt; then \
      echo 'PRESENT: CA certificate bundle'; \
    else \
      echo 'MISSING: CA certificate bundle'; \
    fi; \
    command -v wget >/dev/null 2>&1 || { echo 'BLOCKED: wget unavailable' >&2; exit 65; }; \
    test -s /etc/ssl/certs/ca-certificates.crt || { echo 'BLOCKED: CA bundle unavailable' >&2; exit 66; }


COPY routing/bootstrap.sh /usr/local/bin/oap-routing-bootstrap
RUN chmod 0755 /usr/local/bin/oap-routing-bootstrap

# Route computation remains inside this OAP-controlled service. There is no
# public/demo OSRM runtime fallback.
EXPOSE 10000
ENTRYPOINT ["/usr/local/bin/oap-routing-bootstrap"]
