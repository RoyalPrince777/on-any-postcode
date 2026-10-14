# OAP Hosting — portable recovery runbook

This runbook prepares a provider-independent **candidate**. It does not assert live hosting or authorize traffic switching.

## Preserve before any change
- Keep the existing Render service and immutable GHCR runtime image unchanged.
- Do not uninstall Android applications, rotate or reveal secrets, migrate schemas, or write to production Neon.
- Record the exact reviewed Git commit, image digest and a tested rollback reference.
- Do not promote a host without explicit Founder authority and successful evidence.

## Candidate hosting requirements
- A provisioned Linux container host with HTTPS, persistent secret storage, inbound HTTP routing, egress to the existing Neon database, logs and a reversible deployment.
- Run the reviewed `Dockerfile.runtime` image (or the exact immutable GHCR image already approved), with `OAP_RUNTIME_TARGET=app:app` and `PORT=10000`.
- Copy *only required* environment settings through the candidate host's private secret manager; never commit or print their values. Consult `.github/DEPLOYMENT.md` for required authentication and authority settings.
- Keep Neon production as the existing primary database; no migration or initialization on candidate startup.

## Isolated proof before cutover
1. Verify image digest, source revision, host identity and TLS certificate.
2. Probe candidate `/livez` and `/healthz`; require expected healthy responses.
3. Verify read-only database connectivity and schema readiness without exposing rows, credentials or user identities.
4. Verify public `/world` remains public; private Founder and SMI routes reject unauthenticated users. Follow `.github/DEPLOYMENT.md` for the exact private-route expectations.
5. Verify logs contain no leaked secrets or new 5xx errors; verify backup recovery and a tested rollback.
6. Record evidence in the existing OAP Host Core review. **Do not set self-hosted attestations to true for a third-party provider.**

## STOP conditions
- No real candidate host or credentials; quota suspension; failed TLS, health, database, auth, backup or rollback proof.
- A host requiring public exposure of Neon credentials or an unapproved production data copy.
- Any change that would replace the production origin before independent candidate verification.

## Cutover (separate Founder-approved action)
Only after candidate proof, plan an explicit reversible traffic change and observe the new origin. Keep the old service and rollback path available. Do not silently rewrite Android startup URLs, the SMI gateway upstream or hard-coded Render origins. Audit each dependency before any origin switch.

## Current known blocker (2026-10-14)
Render suspended the existing service for monthly quota exceeded. OAP Host Core has deployment and rollback execution disabled. A separate candidate host has **not** been provisioned or proven.
