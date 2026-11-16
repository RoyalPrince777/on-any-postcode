# OAP first-party VPS gateway (inactive deployment source)

This is a provider-neutral **deployment definition**, not evidence that a VPS, DNS, certificate, or OAP runtime is live. It does not use Render.

## Preconditions

- A purchased, secured Linux VPS with Docker Compose and public TCP ports 80/443.
- IONOS A/AAAA records pointing to its independently verified public address.
- An authorised production database secret and authentication configuration. No secrets belong in GitHub.
- An exact `ghcr.io/royalprince777/on-any-postcode-runtime@sha256:...` digest from the passing `runtime-image` workflow.
- A real TLS contact address for Caddy. Do not copy secrets into this file.

Prepare an untracked local `.env` alongside `compose.yaml` with `OAP_DOMAIN`, `OAP_TLS_EMAIL`, `OAP_RUNTIME_IMAGE`, and `OAP_PRIMARY_DATABASE_URL`; ensure permissions and secret storage are suitable before deployment. Verify all other required application authentication environment variables from the existing OAP configuration; do not launch with a test identity or bypassed Founder gate.

Check configuration with `docker compose config --quiet` before `docker compose up -d`, then independently check DNS/TLS, `/healthz`, and genuine Founder authentication. Run no database migration automatically. This package does **not** start SMI gateway: it stays private and requires a separate reviewed, authenticated ingress design.

Fail closed: do not alter IONOS records or declare Green Gate until the real VPS address, TLS and protected endpoint response are confirmed.
