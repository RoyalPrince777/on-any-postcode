# OAP Host routing — self-hosted OSRM (source only)

**Status: NOT DEPLOYED. No host, public DNS, TLS certificate, live routes,
map tiles, disaster recovery or Founder Final is established by these files.**

This reuses the project's existing root `Dockerfile` and OSRM Greater London
driving graph. The `osrm` container is internal to Docker Compose. A separate
Caddy HTTPS gateway exposes only `GET /route/v1/driving/*` publicly on an
OAP-controlled domain. OpenStreetMap/Geofabrik supplies **source map data**;
route computation runs on the host. This does not claim OSM data ownership.

## Preconditions (must be real)

- An OAP-administered **separate machine/server** with adequate free RAM,
  storage, bandwidth, reliable power, patched Linux, Docker Engine and Compose.
  The OSRM graph extract/build can be memory- and disk-intensive; measure
  these on the actual node before enabling runtime traffic.
- An OAP-controlled public DNS name, e.g. `routes.onanypostcode.com` **only
  if OAP actually controls that name**, with valid A/AAAA records pointing to
  that machine. Use the true owned host; the example is not a claimed DNS record.
- HTTPS: inbound ports TCP 80 and 443, CA issuance/renewal, outbound CA access,
  router/NAT/firewall configuration and real HTTPS verification. Caddy performs
  automatic certificate management only after these prerequisites work.
- Security review before opening a public endpoint: ingress abuse/rate controls,
  patching, access logs that avoid unnecessary route-coordinate retention, OSRM
  graph source integrity, backups of TLS state, failure/rollback and monitoring.
  Compose is **an infrastructure candidate**, not a completed production stack.
- The existing Android OAP Home V2 and protected Termux Home Node remain
  untouched. Do **not** use the limited phone as the assumed OSRM server.

## Build and launch on an actually approved OAP-owned machine

From a separately prepared, reviewed checkout of the **exact authorised**
`on-any-postcode` Git SHA on that machine (not the protected Termux checkout):

```bash
# Replace with a real DNS hostname that OAP controls.
export OAP_ROUTING_DOMAIN="routes.onanypostcode.com"

# Review the resolved config and disk/memory availability first.
docker compose -f deploy/oap-routing-selfhost/compose.yaml config
docker compose -f deploy/oap-routing-selfhost/compose.yaml build osrm
docker compose -f deploy/oap-routing-selfhost/compose.yaml up -d
```

The build uses the repository's existing OSRM Docker image and extracts a
Greater London route graph from the HTTPS OSM PBF source. The HTTPS gateway
allows **only read-only driving routes**. No customer dispatch, finance or
location tracking is part of this Docker Compose file. No public/demo routing
endpoint or automatic alternative provider is configured.

From outside that machine, validate both the real TLS certificate and geometry
from its actual DNS name:

```bash
curl --fail-with-body --show-error \
  'https://routes.onanypostcode.com/route/v1/driving/-0.1687,51.4036;-0.0877,51.5079?overview=full&steps=true&alternatives=false&geometries=geojson'
```

Replace the example host. A successful HTTP 200 **alone is insufficient**:
require `code=Ok`, positive distance/duration and a GeoJSON LineString with
2+ real coordinates.

## Existing OAP routing configuration — no new runtime adapter

Use the same existing three settings in the intended OAP Movement environment
and in the **GitHub Actions repository variables** for the manual gate:

```text
OAP_OSRM_BASE_URL=https://routes.onanypostcode.com
OAP_OSRM_ALLOWED_HOSTS=routes.onanypostcode.com
OAP_ROUTING_OWNED_HOSTS=routes.onanypostcode.com
```

These are example **hostnames, not proof** of ownership or deployment. The
manual gate uses no default host and fails with a zero-network receipt when
unset or unapproved. The OAP Movement product already uses these variables,
with its separate production approval controls. **Configuration/allowlisting
does not certify ownership, operation, route accuracy or launch authority.**

When the manual workflow exists on the repository default branch, a Founder
can trigger it explicitly. The existing `scripts/routing_live_green_gate.py`
then tests 6 bounded warm-up attempts plus **20 real driving routes** using
**4 workers** and a p95 limit of **6 seconds**. It rejects invalid routing
geometry, unreachable hosts, HTTP errors, missing SSL and wrong host settings.
A successful test still needs review of service security, rollback, storage,
host attestation and **Founder Final** before production claims.

No services were created, deployed, restarted or exposed merely by committing
this Compose file. No cloud plan, payment, or external hosting account is
required by this source design, although self-owned hardware, data, electricity,
DNS and connectivity have real costs.
