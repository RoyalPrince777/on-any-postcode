# OAP first-party VPS gateway (inactive deployment source)

This is a provider-neutral **deployment definition**, not evidence that a VPS, DNS, certificate, or OAP runtime is live. It does not use Render. It defines separate public World and private SMI ingress services.

## Preconditions

- A purchased, secured Linux VPS with Docker Compose and public TCP ports 80/443.
- IONOS A/AAAA records pointing to its independently verified public address.
- An authorised production database secret and authentication configuration. No secrets belong in GitHub.
- An exact `ghcr.io/royalprince777/on-any-postcode-runtime@sha256:...` digest from the passing `runtime-image` workflow.
- A real TLS contact address for Caddy. Do not copy secrets into this file.

Prepare an untracked local `.env` alongside `compose.yaml` with `OAP_DOMAIN`, `OAP_SMI_DOMAIN`, `OAP_TLS_EMAIL`, `OAP_RUNTIME_IMAGE`, `OAP_PRIMARY_DATABASE_URL` and `OAP_SMI_GATEWAY_SECRET` (at least 32 high-entropy characters). Set `OAP_SMI_DOMAIN` to a separately verified subdomain under `onanypostcode.global`, not the public apex. Ensure both hostnames resolve to the authorised VPS before TLS issuance. Secure local secret permissions, and supply all real production identity/auth settings through the authorised secret mechanism. The Compose sample does **not** supply all application auth variables, so it must not be deployed without an independent configuration audit. Verify all other required application authentication environment variables from the existing OAP configuration; do not launch with a test identity or bypassed Founder gate.

Review the exact runtime image entrypoint and service credentials before running `docker compose config --quiet`; only then, after operator approval, run `docker compose up -d`. The `smi` service uses the existing `smi_gateway:app` with local WSGI dispatch and a shared internal secret. Both application containers expose port 10000 **inside the Compose network only**, with Caddy publishing HTTPS 443; the gateway is private in *authorization*, not by network reachability. Verify the public World `/healthz`, dedicated SMI `/healthz`, authenticated `/mission/ollama` with real Founder credentials, and unauthorized access rejection independently. A process health response is not proof of authentication, inference, or working chat. Run no database migration automatically.

Fail closed: do not alter IONOS records or declare Green Gate until the real VPS address, both TLS certificates and protected endpoint responses are confirmed. The source-only `https://smi.onanypostcode.global/mission/ollama` shape is an **example**, not a verified live link.
