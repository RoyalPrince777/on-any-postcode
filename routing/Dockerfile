FROM ghcr.io/project-osrm/osrm-backend:v5.27.1

# Runtime image only. Route data is supplied by the OAP-controlled deployment.
# Do not fall back to a public/demo OSRM endpoint.
EXPOSE 10000

CMD ["osrm-routed", "--algorithm", "mld", "--port", "10000", "/data/oap.osrm"]
