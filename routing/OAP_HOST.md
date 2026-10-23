# OAP Host · OSRM route core

This bundle runs the existing OAP-controlled Greater London OSRM graph behind an
HTTPS-only OAP routing hostname. The OSRM port is internal to the compose
network; only the Caddy gateway publishes ports 80 and 443.

## Required host conditions

- OAP-controlled Linux host with Docker Engine and Docker Compose.
- Public DNS for the chosen routing hostname pointing to that host.
- Inbound TCP 80 and 443 available for automatic TLS.
- Enough storage and memory to build the Greater London OSRM graph.
- A rollback reference and Founder approval recorded through the existing OAP
  Host deployment review before production traffic is changed.

## Configure and start

```sh
export OAP_ROUTING_HOST='routing.your-oap-domain.example'
docker compose -f routing/oap-host.compose.yml config --quiet
docker compose -f routing/oap-host.compose.yml up -d --build
```

Then set the GitHub Actions repository variable `OAP_ROUTING_BASE_URL` to the
matching HTTPS origin:

```text
https://routing.your-oap-domain.example
```

The separate blocking `routing-live-ready` job must pass its warmup, 20-request
geometry probe and p95 <= 6 seconds limit before the endpoint has bounded live
routing proof. Software regression success alone does not pass that job. Core
promotion requires both `test` and `routing-live-ready` to succeed for the exact
release SHA. Missing configuration produces a failed receipt without a fallback.

Use only an HTTPS origin on port 443, with no credentials, path, query or
fragment. Render origins and HTTP redirects are rejected. Review OAP control of
the selected host separately: an HTTPS URL or response header does not prove
ownership. Configuration validation and a successful container start are not
deployment, public TLS, route-capacity or infrastructure ownership evidence.

## Boundaries

- No Render endpoint or third-party routing API is used.
- OpenStreetMap extract download is source-data acquisition; live route
  computation remains inside the OAP-hosted OSRM service.
- Dispatch, payment and tracking remain disabled and separately governed.
- Do not expose OSRM port 10000 directly to the public internet.
