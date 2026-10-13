# SMI First-Party Data Sovereignty Protocol

Status: Founder-approved design rule. Enforcement is not implied by this document.
Scope: OAP pull requests, engineering, SMI capability research, Android builds and delivery.

## Authority and source of truth

- OAP-owned repository data and approved first-party services are authoritative for implementation decisions.
- External resources may be consulted for public technical metadata, compatibility facts, and capability discovery. Reading them does **not** authorize importing code, datasets, credentials, services, or private OAP information.
- Do not send private OAP data to external services without explicit authorization and documented necessity.
- Reuse and strengthen existing first-party capabilities. Avoid duplicate systems, regressions and unnecessary dependencies.
- Keep legally required platform dependencies and security controls intact. Do not describe an external Android build tool or platform dependency as OAP-owned.
- No automatic merge into main, signing-key substitution, public release, or production deployment without Founder authorization.
- Security and provenance remain fail-closed: signed artifacts, reproducible package identity, digest evidence, protected secrets, and truthful installation verification.
- CI success proves only the checks actually performed; it does not prove Android device installation or user acceptance.

## Specialist responsibility map

- FOX: capability discovery and failure diagnosis.
- SPIDER: dependency mapping and external-boundary checks.
- NEO: first-party implementation and simplest secure recovery route.
- OCTOPUS: cross-system orchestration and avoidance of duplicate work.
- SERAPH: privacy, signature integrity and fail-closed protections.
- SHERE KHAN: adversarial review of unverified claims.

## Pull-request review contract

Record (1) the first-party source and changed paths, (2) any external metadata consulted and whether anything was imported, (3) new network or third-party dependencies, (4) security/data boundary effects, (5) exact build/test evidence and remaining unverified claims, and (6) Founder approval status for merge or release.

No cosmetic completion percentages, repeated approval loops, demos represented as completion, or weakening of security to force a Green result.

## OAP DATA · SMI 21× Mission-to-100 execution contract

OAP DATA is the provisional name of the OAP-owned metadata and evidence capability, **not** Meta Platforms or an external service. This section defines the review rules; it is not proof that a new service has been deployed.

- SMI and ALL IN coordinate one continuous, bounded implementation mission. Do not stop after every small fix or ask again for approval already granted within scope.
- Remove redundant stages, repeated status-only loops, duplicate reports and simulated success when real tests are available. Preserve necessary security, compatibility, and release gates.
- Prefer one concrete corrective change backed by a failing check or test over repeated speculative configuration changes. Preserve logs and failure context so the next attempt targets the observed cause.
- An SMI specialist name is a **responsibility**, not proof that an autonomous agent ran. Votes and star ratings must be explicitly marked as design judgments unless actual votes/reviews were collected.
- Percentages are permitted **only** when calculated from a fixed, auditable denominator of objective acceptance criteria. Never infer 100% from workflow completion counts alone.
- For Founder Android installation, 100% requires all of: (1) exact-commit build success; (2) package identity and signature verified; (3) Android emulator boot verified; (4) clean APK install verified; (5) OAP Home launcher start and process health verified; (6) Founder device install confirmed; (7) security controls unchanged; (8) authorized release/merge decisions recorded separately. A missing criterion is unverified, not Green.
- A CI workflow that is queued, running, cancelled, timed out or unavailable is not a passing test. Never substitute a demo, mock or assertion for an available installation test.
- Keep merge, signing credentials, production rollout and any external data transfer subject to their existing explicit Founder authorization boundaries.
- Report only changed code, exact commit, real tests, blockers and next recovery action. Avoid repeated mission summaries.
