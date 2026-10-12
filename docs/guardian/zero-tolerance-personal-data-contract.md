# Guardian Zero Tolerance — Founder Personal Data Contract

Status: DESIGN CONTRACT ONLY. No runtime enforcement, monitoring, or legal action is implemented by this document.

## Scope
Applies to personal-data processing across OAP Home, Guardian, SMI, Camera, Mail, My World, Link Up, Maps, SIKA and other OAP services. The Founder is the owner of the private case workspace; this does not grant access to third-party systems.

## Non-negotiable rules
1. Deny by default. Every operation requires an authenticated principal, narrowly scoped purpose, lawful/authorised basis, data classification and valid permission.
2. Collect and retain the minimum necessary; never silently transmit private data or feed it into model training.
3. Audit metadata only: actor, purpose, permission decision, data category, destination class, time, outcome, correlation ID. Never log secrets or raw sensitive content.
4. Block and investigate suspected unauthorised actions; preserve evidence without declaring allegations proven.
5. Do not delete originals before a verified, recoverable export when appropriate; explicit Founder approval for irreversible deletion.
6. No external rights request, complaint, allegation, settlement, solicitor instruction or court filing without explicit Founder approval.
7. All workers and AI agents are subject to the same access checks. No agent can approve its own exception or silently elevate privileges.
8. No false Green: distinguish specified, implemented, tested, runtime-verified and independently verified.

## Founder-private evidence case
Required fields: case ID; company/source (unverified until supported); personal-data category; discovery method; evidence reference and integrity hash; timestamp; legal jurisdiction; claimed right; request/response timeline; status; retention exception; reviewer decision; Founder approval; closure proof.

## Case state machine
POTENTIAL -> EVIDENCE_GATHERING -> VERIFIED_FACTS -> REQUEST_DRAFT -> FOUNDER_APPROVED -> SUBMITTED -> RESPONSE_RECEIVED -> VERIFIED_OUTCOME / DISPUTED / ESCALATION_DRAFT.
Do not automatically advance to VERIFIED_FACTS or VERIFIED_OUTCOME.

## Data-deletion evidence states
NOT_REQUESTED; REQUEST_PREPARED; REQUEST_SENT; PROVIDER_ACKNOWLEDGED; PROVIDER_CONFIRMED; INDEPENDENTLY_VERIFIED; RETENTION_EXCEPTION; UNKNOWN.
Provider confirmation is not independent verification.

## First software proof required
- Pure policy decision function with explicit allow/deny and reason; deny missing or malformed fields.
- Unit tests for unauthorised principal, expired permission, forbidden destination, sensitive-data logging, approval bypass, agent self-elevation, and deletion without recovery.
- Founder-private evidence registry with access-control tests, immutable event history and encrypted storage.
- Cross-module integration tests at real personal-data entry and exit points.
- CI and runtime evidence before claiming enforcement.

## Responsibility map
Bagheera: policy; Seraph: identity/access; Fox: recovery; Spider: lineage; Elephant: evidence; Oracle: verification; OAP IRI: legal workflow; Neo: implementation. These are design roles, not proof of running agents.

## Limitations
Monitoring third-party databases without authorisation is prohibited. Erasure rights may have legal exceptions. A privacy incident does not automatically establish a legal violation or compensation entitlement.


## Second mandatory protocol: Founder-authorised OAP-wide access and accountability
The Founder needs a unified, secure inventory of *all OAP-controlled* services, accounts, data stores, permissions, logs, integrations and personal-data flows. This is not unrestricted access to external companies or an exemption from other users' privacy.

- **Inventory:** catalogue every OAP module, service, database, worker, repository, deployment, backup, device integration and third-party processor; classify owner, environment, sensitivity, location and proof status.
- **Founder control plane:** authenticated Founder dashboard for service discovery, access review, data export, request approvals, emergency lockdown, recovery and audit. Strong MFA and reauthentication for sensitive operations; least-privilege, short-lived credentials and break-glass access with independent logging.
- **Separation of duties:** privileged access to other users' information is exceptional, purpose-limited, logged and reviewed; do not treat Founder status as consent to unrestricted inspection of private user content.
- **Two connected protocols:** (A) Personal Data Zero Tolerance prevents unauthorised processing and prepares rights enforcement; (B) OAP-wide Access & Accountability ensures visibility, security, governance and recoverability of OAP-operated systems. Both share identity, policy, audit and evidence infrastructure.
- **Every access event:** actor, resource, purpose, authorisation, time, action, outcome and case correlation ID; do not record raw personal data or secrets.
- **External provider boundary:** inventory contracts, lawful API permissions, data exports and subject access rights; do not claim access to Google, Meta, telecoms or other third-party databases.
- **Security gates:** deny-by-default policy tests, Founder MFA, role-scoped access, encrypted evidence, tamper-evident audit, backup recovery, revocation and incident drills. Any unverified gate stays unverified.
- **No surveillance loophole:** security monitoring must be proportionate and compliant with applicable privacy and employment law.
- **First integration target:** read-only OAP service inventory and policy decision API; then protected evidence registry; then audited Founder dashboard and integration tests.
