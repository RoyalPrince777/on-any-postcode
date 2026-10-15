# OAP Routing — independent OSRM deployment

This is a deployment runbook, **not** evidence of a running server or a passed Green Gate. It reuses `routing/Dockerfile`, `routing/bootstrap.sh` and `routing/compose.yaml`. Do not route production traffic to an unverified host.

## Prerequisites

- An OAP-controlled Linux host with Docker Engine and Docker Compose plugin, enough free storage and memory to download and preprocess the selected OSM extract, and reliable outbound HTTPS access.
- Disk capacity and OSRM preprocessing time depend on the selected region. Start with the existing Greater London extract; do not claim worldwide coverage.
- A domain controlled by OAP, TLS certificate and an authenticated/controlled reverse-proxy deployment if public access is intended. The Compose file intentionally exposes **only** `127.0.0.1:10000`.
- Confirm licensing and attribution requirements for OpenStreetMap/Geofabrik data before publishing a service.

## Prepare and start on the host

From the repository root:

```sh
docker compose -f routing/compose.yaml config --quiet
docker compose -f routing/compose.yaml build osrm
docker compose -f routing/compose.yaml up -d osrm
docker compose -f routing/compose.yaml logs --follow --tail=100 osrm
```

The first start downloads and preprocesses the road graph; it can take time and needs sufficient storage. The named volume `routing-data` persists the graph across container restarts. Inspect logs and disk capacity rather than assuming the container is ready.

## Local smoke proof (run on the host)

```sh
curl --fail --show-error --max-time 20 \
  'http://127.0.0.1:10000/route/v1/driving/-0.1687,51.4036;-0.0877,51.5079?overview=full&steps=true&alternatives=false&geometries=geojson'
```

Check the JSON response contains `code: Ok`, nonempty `routes[0].geometry.coordinates`, positive distance and duration, and a plausible Greater London route. A successful HTTP response alone is insufficient.

## External Green Gate (separate proof)

Only after configuring a controlled HTTPS reverse proxy to the loopback port, validating its TLS and access controls, and proving real routing on the **intended** hostname, configure the repository variable `OAP_ROUTING_GREEN_GATE_BASE_URL` with its exact `https://` origin (no path, credentials, query or fragment). The governed CI probe is fail-closed when this variable is absent. Do **not** point the variable at an unrelated public OSRM demo or a billing-suspended endpoint.

The external Green Gate checks real route geometry and bounded request capacity; local smoke checks and unit tests do not replace it. Preserve the existing first-party federation configuration and only change `OAP_OSRM_BASE_URL` or shard URLs when the new route engine is verified and authorized for the target environment.

## Rollback / recovery

```sh
docker compose -f routing/compose.yaml ps
docker compose -f routing/compose.yaml logs --tail=100 osrm
docker compose -f routing/compose.yaml down
```

`down` leaves the named road-graph volume intact. **Do not** run `down --volumes` unless deliberately deleting the persisted routing data. If validation fails, leave the external Green Gate blocked and retain the previous approved routing configuration.
