# OAP Digital Organism — 24/7 Worker Opt-In

This document describes the final infrastructure step for continuously running the existing bounded Digital Organism runtime. It does **not** authorize or create infrastructure by itself.

## Current boundary

The active root `render.yaml` remains free-mode and contains no background worker. The separate file `deploy/render.organism-worker.opt-in.yaml` is an explicit deployment candidate only.

Applying that candidate would create a paid Render background worker named `oap-organism-runtime`. Human Authority must explicitly approve the infrastructure and billing decision first.

## What the worker runs

Start command:

```text
python -m mission_control.organism_worker
```

The existing PostgreSQL runtime provides the durable queue, schedules, leases, retries, dead-letter records and receipts. No Redis/Key Value service is required.

Scheduled bounded work:

- `RUNTIME_HEARTBEAT` every 60 seconds.
- `RUNTIME_HEALTH_PROBE` every 300 seconds.
- OAP CORE bounded autonomy status/cycle.
- SMI bounded autonomy from live 3x7 / 21-gate production evidence.
- Whole Digital Organism bounded autonomy/coherence/recovery/growth review.

## Authority invariants

The worker may observe, review, retry safe work, recover stale leases and create non-consequential proposals. It cannot independently approve or execute consequential actions.

Always locked behind the governed Human Authority / Living Kernel path include deployment, public publishing, production migration, permission/role changes, payment capture, money transfer, driver dispatch, eSIM activation, carrier switching, public precise tracking and self-application of improvements.

Every runtime handler result must contain `consequential_action: false`; otherwise the worker rejects the result and moves it through the retry/dead-letter path.

## Required secrets/configuration

The opt-in Blueprint declares the following as Render-managed values rather than repository secrets:

- `DATABASE_URL` — production PostgreSQL connection.
- `OPENAI_API_KEY` — used only as production SMI provider-configuration evidence and by normal SMI provider routes; the autonomy health cycle itself does not perform a completion.

Render supplies the deployed Git commit through its runtime environment, and the worker records that revision in heartbeat evidence.

## Graceful shutdown

The worker already handles `SIGTERM` / `SIGINT`, marks itself `DRAINING`, stops taking new jobs, finishes the current bounded job, records a final `STOPPED` heartbeat and exits. The candidate Blueprint sets `maxShutdownDelaySeconds: 120` to give that path time to drain.

## Promotion checklist

Before creating the worker service:

1. Human Authority explicitly approves the paid always-on worker.
2. Confirm `0004_organism_runtime` is applied and checksum-verified in production.
3. Confirm `DATABASE_URL` and provider configuration are available to the worker without copying secrets into Git.
4. Create exactly one worker from the opt-in Blueprint or equivalent Render settings.
5. Verify the worker revision equals current production main.
6. Verify a fresh `oap_runtime_workers.heartbeat_at` record appears.
7. Verify heartbeat and health jobs reach `SUCCEEDED` receipts.
8. Verify OAP CORE, SMI and organism results all remain `consequential_action: false`.
9. Verify no error/dead-letter spike after launch.
10. Only then mark continuous 24/7 autonomy green.

Until those runtime freshness checks exist, the truthful status remains **deployment-ready 🟢 / continuous 24/7 execution 🟠**.
