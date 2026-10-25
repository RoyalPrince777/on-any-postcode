# OAP Mail inbound delivery boundary (design gate)

Status: **NOT IMPLEMENTED / NOT LIVE**. This document is not an authorisation to change IONOS DNS, enable sending, migrate production data or claim mailbox delivery.

## Evidence from existing source

- `mission_control/mail_mailbox.py` is an owner-scoped, read-only projection of `oap_mail_items`; its status explicitly reports `inbound_transport_built: false`.
- `mission_control/mail_routes.py` currently guards mailbox routes with founder-only authentication.
- `mission_control/mail_outbound.py` provides an explicitly gated, allowlisted outbound SMTP relay, not inbound reception.
- `mission_control/mail_preflight.py` requires independent database/recovery evidence before release.

## Smallest safe next implementation

1. Confirm the intended mail authority: continue using IONOS-hosted receiving or deploy an OAP-owned inbound SMTP service. Do **not** silently equate the two.
2. Keep existing IONOS MX/SPF/DKIM/DMARC unchanged until receiving ownership, mail routing and rollback are demonstrated.
3. Introduce a separately authenticated inbound adapter only after defining recipient-to-owner mapping, message size limits, MIME parsing, attachment policy, duplicate suppression, rejection/quarantine handling and audit retention.
4. Store admitted messages in the existing canonical mail store via a bounded, transactional write path; do not create a second mailbox database. Never expose this adapter as an unauthenticated HTTP ingestion endpoint.
5. Test rejection of forged recipients, invalid sender assertions, oversized messages, duplicates, malformed MIME, cross-owner reads, and missing database readiness. Confirm legitimate delivery using a real external mailbox and a reply, with redacted logs.
6. Keep public multi-user mail disabled until explicit access controls and account recovery are independently verified; existing founder-only routes do not establish public readiness.

## Release evidence required

- Domain/DNS control and current records verified by operator (historical screenshots are not current live DNS proof)
- Inbound transport deployed and authenticated; end-to-end delivery to canonical mailbox verified
- Outbound relay and real recipient delivery verified (SMTP acceptance alone is insufficient)
- Database target, backup integrity, isolated restore and readback evidenced
- Abuse controls, privacy safeguards, tests and Founder Final approval

Overall VPI: **N/A** until measured evidence exists.
