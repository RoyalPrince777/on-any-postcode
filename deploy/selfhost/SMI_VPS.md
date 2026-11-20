# SMI on the Founder-controlled VPS

Deployment source only. No VPS, DNS, TLS, model, worker, signed execution or migration is certified by these files. This is the private SMI extension of deploy/selfhost. The OSRM routing deployment under deploy/oap-routing-selfhost is a separate service; do not run a second 80/443 edge on the same host. Preserve its existing PR and review one shared edge before co-hosting.

## What this corrects

The base gateway starts only OAP World. It deliberately does not start the private SMI gateway, a model, or an organism worker. The Sites dashboard currently records scope signals in its own store; these are not the canonical signed, single-use ActionPlan receipts.

The optional compose.smi.yaml overlay starts the existing smi_gateway:app in local-dispatch mode on internal port 5000, the existing organism worker, and a local Ollama model service. Caddy exposes HTTPS for separate public World and private SMI hostnames. There is no Render upstream hop, external AI fallback, duplicate queue, or replacement approval authority in this overlay.

The organism worker still runs its existing heartbeat and health-probe handlers. Code actions use the existing Founder tools, signed approval service and Living Kernel. That allowlist permits branch creation, file writes and PR creation. It does not merge, deploy, spend or grant broad shell execution.

## Required before deployment

- A purchased Linux VPS, administrator access, Docker Engine and Compose. This source does not purchase or configure a server, firewall, SSH, DNS or billing.
- Distinct, Founder-authorised OAP_DOMAIN and OAP_SMI_DOMAIN hostnames, and OAP_TLS_EMAIL. Confirm the actual server IP before any DNS cutover. The existing IONOS default-site IP is not a VPS.
- OAP_RUNTIME_IMAGE pinned to a verified ghcr.io/royalprince777/on-any-postcode-runtime@sha256 digest, with its exact 40-character OAP_ENV_REVISION and passing governed checks. The image must contain the local-dispatch gateway, inference facade and canonical execution bridge.
- OAP_OLLAMA_IMAGE pinned to a reviewed ollama/ollama@sha256 digest, OAP_SMI_MODEL naming a reviewed model to be installed, and OAP_VPS_WORKER_ID naming one stable unique worker.
- The existing database schema and Founder identity. Do not initialise a new ledger or run migrations automatically. Reusing the existing Neon database is a transitional hosting arrangement; it is not proof of fully self-hosted data custody.

Create root/server-owner readable files (mode 600), excluded from Git:

- `.env`: the non-secret compose variables above and the existing base gateway's OAP_PRIMARY_DATABASE_URL secret. Keep every credential out of terminal output.
- `.env.smi`: existing DATABASE_URL (or canonical database secret), OAP_SESSION_SECRET, OAP_HUMAN_AUTHORITY_ID, OAP_SMI_GATEWAY_SECRET (at least 32 characters), and existing Founder authentication settings. The governed write bridge additionally needs its separately scoped OAP_GITHUB_TOKEN and OAP_APPROVAL_SIGNING_KEY. Preserve existing identities and credentials; do not create a test Founder or enable an authentication bypass.
- `.env.worker`: only the canonical database credential required by mission_control.organism_worker. Do not give this health worker the GitHub token or approval-signing key.

Do not copy a blanket production environment into these files. Review boot/migration flags before loading an existing configuration. Do not set sovereignty attestations or mark Green merely because this is a VPS.

## Start after the host and release are authorised

From deploy/selfhost, validate without printing resolved secrets:

```bash
docker compose -f compose.yaml -f compose.smi.yaml config --quiet
```

Pull the reviewed images, start Ollama, and install the selected model:

```bash
docker compose -f compose.yaml -f compose.smi.yaml pull
docker compose -f compose.yaml -f compose.smi.yaml up -d ollama
docker compose -f compose.yaml -f compose.smi.yaml exec ollama ollama pull "$OAP_SMI_MODEL"
docker compose -f compose.yaml -f compose.smi.yaml up -d
```

OAP_SMI_MODEL must be exported in the operator shell for the model-pull command; Compose's `.env` loading does not export shell variables. Pin and review the model artifact; measure memory use and actual response latency on the purchased host before claiming performance.

Public host ports remain only 80/443 on Caddy. SMI port 5000 and Ollama port 11434 are Docker-network-only. Do not publish model, database or unauthenticated management ports.

## Prove operation

Check real DNS and TLS; original Founder sign-in; anonymous denial on private SMI, Founder tools and execution routes; original CSRF checks; the correct image/source revision; a fresh VPS worker heartbeat and durable runtime receipts; actual local inference with compatibility fallback disabled; and genuine streamed work-stage events in chat. A /healthz 200 proves process availability only.

Then verify one exact signed ActionPlan through the canonical Founder tools. Missing evidence, stale/consumed receipts and mismatched action digests must remain blocked. Do not replay the Sites dashboard's old 'Signal saved' records as executable approvals. Its execution connection still requires authenticated integration with this canonical flow; provisioning a VPS alone does not implement that integration.

Preserve the existing Evidence Site and Command Centre. The first-party private SMI origin uses the existing Founder login, not ChatGPT authentication. A Sites preview is not the independent runtime.

## Stop and rollback

Stop only the new SMI services with the same compose file pair:

```bash
docker compose -f compose.yaml -f compose.smi.yaml stop organism-worker smi ollama
```

Restore Caddy to the existing base configuration using `docker compose -f compose.yaml up -d edge`. Keep model/data volumes and audit records. Never use `down -v` as an operational rollback. Confirm public World and private anonymous denial after rollback. Restore the prior image digest only under the existing release discipline.
