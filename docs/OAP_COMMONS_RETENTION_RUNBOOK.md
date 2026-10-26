# OAP Commons retention — first-party operator

Status: **draft code, not deployed or scheduled**. The database is OAP's existing
canonical PostgreSQL. No GitHub-hosted runner, vendor transfer, new agent
passport, or public vote is needed.

## What is governed

- Private, consented member proposal content is hidden from member and Founder
  lists after **90 days from creation**; this is a display-access guard, not
  deletion from the database.
- Owner withdrawal redacts the JSON proposal text and archives the record.
- Founder can issue a private **nonbinding** review; never a court ruling or
  public election outcome.
- The bounded retention operator redacts older unarchived records in-place.
  Its receipt is recorded with actor type **SYSTEM**, authority level **0**,
  label `OAP_COMMONS_RETENTION_SERVICE`. It is not a new AI agent or human
  Founder and cannot record reviews, votes or approvals.
- The canonical audit ledger retains an actor/target identifier and metadata.
  Starting with this change, **new proposal intake receipts no longer store
  a SHA-256 fingerprint of the free text**. Older immutable receipts may
  contain such fingerprints. Historical audit retention, backup copies,
  personal-data rights and lawful exceptions require separate assessment.

## Trusted-runtime commands (no credentials in code, CI or output)

Run on an already-secured OAP first-party runtime with configured canonical
PostgreSQL; **not** on a public GitHub runner:

```bash
python -m mission_control.oap_commons_retention --dry-run

OAP_COMMONS_RETENTION_ENABLED=1 \
  python -m mission_control.oap_commons_retention --apply \
  --batch-size 100 --max-batches 10
```

Exit status: `0` means clear or dry-run succeeded; `2` disabled by operator;
`3` database/audit unavailable; `4` backlog remains after batch cap.
Output contains **only counts/status**, never proposal text, member names or
database secrets. Invalid batch sizes are refused. The operator uses a
PostgreSQL advisory transaction lock for write/audit consistency.

A trusted OAP runtime scheduler may invoke the above *daily*, with an
operator-owned service configuration, monitoring on any non-zero exit status,
and retry/backlog handling. **No scheduler has been installed or verified
by this PR**. A CI passing result is not a live 90-day erasure guarantee.

## Production privacy/security acceptance still required

- Verify real HTTPS authentication and CSRF on the deployed app (member vs
  Founder), negative cross-account access, and no private text in public logs.
- Confirm the scheduled job runs under a least-privilege runtime identity and
  cannot reach unrelated data. A first-party service is distinct from an SMI
  agent/Passport and has no permission to judge, publish or vote.
- Test an actual aged record, redaction and audit chain persistence on a safe,
  consented non-production database, then validate live operator receipts.
- Confirm backups, retention exceptions, subject-access/deletion requests,
  audit metadata and historical hashes with a qualified privacy reviewer.
- Guardian/HRM evidence and Founder Final before any Green or production claim.

OAP Law: **proven draft code is not production authority**.
