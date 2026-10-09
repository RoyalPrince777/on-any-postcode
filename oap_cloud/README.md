# OAP Cloud V1 — Founder-first, global-ready

This initial control-plane blueprint is **not registered** in the production Flask application and does not provision storage, compute or any cloud infrastructure.

- Endpoint after deliberate integration: `GET /cloud/v1/status`.
- Fail-closed token guard: set `OAP_CLOUD_FOUNDER_TOKEN` as a high-entropy secret on a private, HTTPS-only deployment. This standalone bootstrap token is not a replacement for the existing OAP Founder session/Guardian authentication.
- Do not expose this endpoint publicly or register it until integrated with OAP's existing Founder authorization, rate limits, audit trail and security tests.
- Never place secrets in Git.
- Storage, AOSP workers, artifacts and first boot remain unproven.

Next: inspect existing Founder authentication contracts, integrate without duplicate identity paths, add tests, then provision storage and an isolated temporary Linux AOSP worker.
