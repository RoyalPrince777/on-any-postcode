# OAP Host — SMI Alliance Recovery Contract

Status: **design and implementation contract only**. No alternative host, failover, or production restoration is attested by this document.

## Authority and division of work

- **SMI / Founder**: policy, priorities, final authorisation for consequential production changes.
- **Queen Bee**: coordinate bounded workers, assign incident tasks, deduplicate jobs, collect signed/traceable receipts; never self-authorise production traffic switches.
- **Spider**: maintain the dependency graph (origin, runtime, routing, identity, database, storage, mail, SIKA, OAP Home); identify blast radius and required checks. A missing dependency is unknown, never green.
- **Octopus**: evaluate independently provisioned host candidates, orchestrate preflight and reversible recovery; never substitute a simulation for live host evidence.
- **Matrix**: Architect reviews design; Keymaker validates access and routing; Seraph protects trust boundaries; Oracle evaluates risk; Neo detects anomalies; Morpheus plans recovery; Trinity coordinates secure action. Tank protects existing production; Dozer performs bounded repairs. Agent Smith challenges evidence and downgrade risks.

## Incident: Render workspace quota suspension

The 2026-10-14 incident affected 18 Render services, including the public origin and routing. An external routing probe failing while the provider is suspended is a valid red gate, not a reason to disable the probe. Existing Neon production data and Android installs must be preserved.

## Required live candidate evidence (all mandatory)

1. **Identity**: record the candidate host owner, provider, region, immutable runtime image digest, configuration version, and operator authority.
2. **Network**: valid TLS chain, correct hostname, no unapproved open admin/database ports, controlled outbound access.
3. **Runtime**: application actually starts and serves `/livez` and `/healthz` with acceptable responses; no stale cached or static substitute.
4. **Data**: authorised read-only database connection verified; no implicit migrations, schema changes, secret disclosure, or production writes during preflight.
5. **Trust**: Founder authentication, private routes, session/cookie policy, CSRF, and unauthenticated-denial checks proven against candidate.
6. **Dependencies**: routing and other required service dependencies independently tested; unavailable dependencies remain red and do not become waived.
7. **Recovery**: logs/metrics, backup and restore evidence, reversible origin change, rollback operator and tested rollback route documented.
8. **Cutover**: explicit separate Founder approval, recorded before switching real users or DNS; perform post-cutover health and rollback checks.

## Machine-readable receipts

Each check should emit: `incident_id`, `host_id`, `check_id`, `observed_at`, `result` (PASS/FAIL/UNKNOWN), `evidence_ref`, and `operator`. Aggregate readiness is PASS **only if every mandatory check is PASS**. Missing, expired, or untrusted evidence is UNKNOWN; any FAIL/UNKNOWN blocks cutover.

## Non-negotiable boundaries

- Do not call third-party VPS infrastructure self-hosted merely because OAP operates its containers.
- Do not expose OAP Home/Termux as a public fallback or silently redirect private app traffic.
- Do not modify Render billing, provision paid infrastructure, rotate production secrets, change DNS, or merge/deploy from this document.
- Do not disable real routing gates, security checks, or CI failures to manufacture Green.
- Upgrade-only: reuse existing OAP Host Core and the portable recovery runbook, without replacing functioning services.
