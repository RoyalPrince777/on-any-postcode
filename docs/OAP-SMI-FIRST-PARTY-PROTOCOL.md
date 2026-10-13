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
