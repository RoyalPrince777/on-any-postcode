# Founder 429 Recovery Gate

Status: diagnostic only. This change does not deploy, merge, weaken authentication, disable rate limiting, or expose the private dashboard.

## Incident model

The affected handset receives HTTP 429 before the SMI Founder recovery handler can establish a bounded Founder session. The existing `/auth/recover-founder` GET is not itself app-rate-limited, so an upstream edge or gateway remains the leading boundary until response evidence proves otherwise.

PR #217 adds `/auth/founder-entry` as a second route to the same Founder handler. Because it shares the same application handler and security contract, it is a real bypass only if the upstream 429 is path-specific.

## Production proof gate

From the affected handset, through the same network and production hostname, compare anonymous GET responses for:

1. `/auth/recover-founder?next=/mission/ollama`
2. `/auth/founder-entry?next=/mission/ollama` (only after that route is independently approved and live)

Record only: timestamp, HTTP status, Retry-After if present, Server/Via/edge request identifier headers if present, and whether an application Founder Access page was reached. Do not record or submit the Founder password/code for this diagnostic.

### Decision

- old=429, alternate=200: evidence supports a path-specific upstream rule; the alternate lane has incident value.
- old=429, alternate=429: do not treat a path rename as a fix; trace the host/IP/device/cookie/service-wide upstream limiter.
- app response reached and then 429: reopen application/gateway rate-limit analysis.

## Security invariants

- Founder-only remains fail-closed.
- No signup is enabled.
- No password/code bypass.
- No private dashboard anonymous access.
- Do not remove rate limiting globally to recover access.
- Prefer bounded, auditable recovery over broad exemptions.
