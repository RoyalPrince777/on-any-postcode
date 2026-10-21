# OAP Cloud — unified infrastructure contract (Founder direction C)

Status: **architecture contract plus an unmerged local private-storage candidate; not deployed**. One OAP Cloud provides compute and storage foundations. OAP Host runs applications; OAP Drive is the file interface; OAP Home is a private node. Reuse existing systems; do not create a parallel identity, payments or SMI ledger.

## Implemented boundary (unmerged candidate)
- Only local personal private-object put/get code exists. The caller-supplied identity parameters are **not authentication**; no user-facing route may use them without a separately verified server-side principal.
- Business authorisation, public publication/read, signed links, revocation, malware scanning, audit, durable storage, encryption-at-rest validation and backup restore are **not implemented or verified**.
- Public access must remain impossible until explicit, independently authorised publication and revocation exist. No filename or logical prefix grants public access.

## First bounded release
- Retain existing OAP World front door and existing routes. Do not change Android startup, DNS or production origin.
- A private Founder-only Cloud control surface may eventually show host/storage health, quotas, evidence and recovery; **no live controls are claimed** here.
- Storage partitions: `personal/{owner_id}` private, `business/{business_id}` role-controlled, `public/{publisher_id}` explicitly published. Names are logical prefixes, not proof of bucket isolation; enforce separate server-side authorisation and storage policies.
- File upload must enforce ownership, size/type limits, malware scanning or quarantine, encryption at rest/in transit, audit events, and safe content-disposition. Public reads require an explicit publish action; never infer publicity from a filename or URL.
- Signed access must be short-lived, scoped to a specific object and operation, and revocable. Never expose storage credentials or allow arbitrary object keys supplied by clients.
- Backups must be encrypted and independently restorable; do not call backup complete until an actual restore test passes.
- SIKA billing remains disabled until lawful payment infrastructure and reconciliation are independently verified.

## Route C: £0-first, paid fallback
- Founder Android + Termux is an administration terminal, not assumed always-on public hosting.
- Investigate an eligible free Linux host; verify actual availability, account requirements, capacity and egress limits before relying on it. No provider is selected or provisioned by this contract.
- A paid VPS is a fallback only after Founder authorises the specific provider and cost. Do not provision billable infrastructure automatically.
- Deploy a reviewed immutable runtime image with private secret management, TLS, /livez, /healthz, authentication checks, read-only database proof, monitoring and rollback. No production Neon writes during candidate validation.
- Preserve Render and all existing origins until a separate Founder-approved cutover with independent live evidence.

## Evidence gates (no cosmetic percentages)
1. **Design:** this contract and security boundaries reviewed.
2. **Implementation:** actual cloud storage/compute code and tests exist; no placeholder UI accepted as operational.
3. **Isolation:** prove cross-owner and cross-business denial, private-by-default and explicit publication/revocation.
4. **Reliability:** demonstrate real upload/download integrity, backup restore, incident logging and recovery.
5. **Hosting:** candidate server provisioned; verify HTTPS, immutable image, /livez, /healthz, auth and rollback.
6. **Operations:** Guardian and HRM record independent evidence; Founder authorises production promotion separately.

**Current truth:** architecture contract and unmerged local private-object candidate only; no OAP Cloud storage deployment, authenticated OAP Drive integration, public publishing, independent host, live availability proof or backup-restore proof. Existing Render billing suspension cannot be cleared by changing this document or disabling the routing Green Gate.
