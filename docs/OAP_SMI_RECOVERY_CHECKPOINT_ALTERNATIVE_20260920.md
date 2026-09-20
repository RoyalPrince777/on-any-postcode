# SMI 25% Recovery — independent checkpoint path (Founder-approved for review)

Status: 🟣 OPERATOR RUNBOOK / REVIEW-ONLY — NOT an executed backup, restored database, writer write, deployment, merge, or Green Gate. The Founder approved pursuing this *alternative recovery route* on 2026-09-20. A green symbol is approval to proceed under evidence gates, not a claim of completion or blanket permission to mutate production. Preserve the original 4-stage law: **25% Rollback / Recovery → 50% Runtime Guard → 75% Aegis Isolation / Recovery → 100% Green Gate + Founder Final**. This document operates INSIDE 25%; it does not introduce a stage or silently change its success criterion.

## Retain prior proven evidence

- Existing independent snapshot-derived Neon recovery copy matched **36/36 original public BASE TABLES**, 319 stored rows, stable count/content-derived digests; 215 internally linked stored audit events. This sub-proof **PASSED 🟢** at inspected checkpoint and must not be rerun merely to create more activity.
- A 2026-09-19 **09:43–09:45 UTC** restore unexpectedly finalised and temporarily moved the original RW endpoint; it was subsequently reattached. Preserve the incident in `historical_attempts=UNKNOWN`. Neither matching copies nor audit adjacency establish that every attempted action was durably recorded.
- Original Neon `blue-heart-80559481` / `br-little-pine-arfbcpln` is the default/primary source; `ep-square-poetry-ar044jl7` remains attached. The recovered branch `br-nameless-forest-arjp9w0y` and dedicated read-only compute `ep-dark-glade-arb421ya` remain separate. Control-plane states may change after this checkpoint: independently recheck before any approved action.
- Original Neon snapshot `snap-nameless-tooth-arw9094g` is manual; the inspected automatic snapshot schedule is empty. Do not equate a single snapshot with recurring backups.
- Independent Render `oap-smi-hrm-fallback` `dpg-dahh4fss728c73b2sik0-a` is listed as available and free, scheduled to expire **2026-10-10T20:25:35Z**. The connector reached TLS handshake failure (`SSL/TLS required`) *before* running read-only SQL: never interpret this as no rows. Preserve separately and independently if it actually contains records.
- SMI Render live deploy observed 2026-09-20: `dep-dan7v90ae00c73dr528g` at `4839e40941ecdf48e982d9b91f567165f8d4be19`, SMI auto-deploy off. A deploy revision is not proof of actual main or independent HRM writer identity.

## Recovery 25% — Phase A: source attribution (read-only)

- Review focused **PR #452** (passive Founder-only selected-main / HRM hostname fingerprints, passive GET, separate CSRF-protected POST proof, no SQLite durability false-positive). Its earlier CI #2047 passed *that head*, but it is unmerged, not live. Do NOT call the currently deployed `GET /smi/brain/receipts` as a passive diagnostic: on the inspected live revision this endpoint still performs a proof write on GET.
- Release the passive diagnostic only under **separate, bounded Founder authorisation**, actual-head CI, least privilege, independent security review and rollback plan. Do not combine it with PR #443's unrelated memory-sync specification or UI PR #456.
- Match **both** actual selected main SMI authority and the independent HRM writer to provider identities. Compare source class, normalized host fingerprint, selected database, branch/compute where available and read-only session identity. Hostname hash alone cannot establish DB, branch or writing rights. Never print URLs, passwords, private record payloads or unredacted connection parameters in a PR comment.
- If the actual writer store remains ambiguous or a second app writer can change the authoritative record unexpectedly: **BLOCK**. A configured URL or startup read-only probe is insufficient.

## Recovery 25% — Phase B: best-available incident reconciliation (read-only)

- Read first-party request/audit/queue IDs and timestamps for 2026-09-19 09:43–09:45 UTC from **each proven store**. Preserve raw archives privately; publish only redacted IDs/hashes/counts and availability labels. Correlate IDs and dedupe only *after* inspecting differences; never delete the original or unique records.
- Obtain an authorised TLS-capable read-only connection to separate Render Postgres before expiry (e.g. authorised Render-internal runtime or secured `psql`/`pg_dump` over required TLS). The existing Render SQL connector currently fails TLS. A transport error means **uninspected**, not empty. Do not log or put PG URLs/passwords into GitHub/ChatGPT. Do not change firewall/env, migrate, or repoint writers as a troubleshooting shortcut.
- Classify each attempted operation as `recorded`, `correlated`, `conflicting`, or `unobservable/UNKNOWN` with concrete first-party source identifiers. No available server logs in an incident interval is not evidence there were no attempted operations.
- Record known unknowns as **explicit scoped exceptions**; never assert historical zero loss. If independent Render records cannot be inspected, the whole 25% gate remains blocked.

## Recovery 25% — Phase C: independent backup + offline restore (no Neon restore API)

- Once provenance is known, approve an operator-controlled *read-only* PostgreSQL custom-format logical archive (`pg_dump`) of EACH selected authoritative store; preserve separate encrypted, access-controlled artifacts and SHA-256 checksums, creation time, selected sanitized source fingerprint, PostgreSQL version and verified archive listing. `pg_dump` by itself proves no restore and has not been run by this document.
- Restore archives via `pg_restore` **only into a brand-new disposable offline PostgreSQL instance** with no live service credentials, network routing or production host. Never use the production URL, the source name as destination, Neon `restore_snapshot`, implicit finalize, target-branch promotion or existing production endpoint. An external offline store must not become a second live writer.
- Validate schema, all tables (not only public when additional schemas matter), deterministic per-record digests, row IDs and receipt/audit hash continuity from archive to isolated restored store. Retain encrypted archive and machine-readable verification receipt. Do not claim a fresh checkpoint for the historical 09:43–09:45 window just because older stores match.
- If the chosen backup target cannot be safely isolated, if archive encryption/restore verification fails, or if production invariant checks are not available: **BLOCK**.

## Recovery 25% — Phase D: fresh durable proof epoch (new scoped action)

- ONLY after source attribution/approval: a separate explicit Founder-authorised, idempotent **non-user-content** receipt to the one chosen durable HRM writer, with stable correlation ID, expected receipt kind and checksum. Do not enable money, payments, public A6, ordinary user operations, or broad auto-recovery. The passive GET and SQLite fallback must NEVER be counted as a durable receipt proof.
- Verify commit and an **independent new-session readback** from the same selected durable store, then back up and restore this **new** checkpoint offline and independently check the same ID/hash plus audit trace. Also independently prove the main SMI writer's selected store identity; HRM success alone is not its proof.
- Capture audit receipt with `checkpoint_start_utc`, source fingerprints, sanitized IDs/digests, original branch and endpoint pre/post invariants, selected writer, independent HRM proof, archive/checksum/restore readback and `historical_09_43_09_45=UNKNOWN`. Never insert this historic exception into a false `no_loss=true` claim.
- If the original backend is inactive, TLS proof cannot complete, durable write flag is disabled, a second writer appears, receipt fails, or recoverability from new checkpoint cannot be independently restored: **BLOCK and preserve the original state**.

## Founder Green Gate scope

A 25% **scoped operational-recoverability-from-new-checkpoint** 🟢 may be *considered* only when Phases A–D have independently verified receipts and the Founder explicitly accepts the truthful limited scope and irreducible historical UNKNOWN. If the required claim is **zero historical loss during the incident**, or policy disallows unresolved unknown operations, the 25% gate remains 🔴 despite successful new-checkpoint work. Never turn 50/75/100 green by implication; enter them sequentially with their own evidence and Founder final at 100%.

**Prohibited by this runbook alone:** production writer/URL/env changes, paid plan creation, migrations, database writes, restores, branch/endpoint reassignment, GitHub merge, Render deployment, automatic receipt proof on GET, leaked connection strings/private data, arbitrary gap forgiveness. An audit-comment or this document is NOT a live SMI-memory sync receipt.


## 2026-09-20 operational evidence checkpoint (read-only)

- GitHub governed CI `#2087`, run `35501107817`, completed **SUCCESS** on this runbook PR head `ad690a7471fa05f1344543f808fc1df36635a751` (this is document/code-level checks, **not** an executed restore). Focused diagnostic PR #452 CI `#2047`, run `35439342845`, succeeded on its head `38895b4926078c0e132c5843c92599b3d595f636`. Neither focused PR nor runbook PR has been merged/deployed.
- Neon provider listing still shows original primary/default branch and original RW endpoint attached, both recoverable branch and RO endpoint separate; both endpoints were **idle** at inspection. Avoid waking either merely to reconfirm the already-PASSED 36/36 historical copy comparison.
- Fresh Render current-live-revision log `2026-09-19T12:28:06Z`: `oap_smi_database_certification` = PostgreSQL/`fallback_override`, reachable+initialized, pending migrations 0, checksum mismatches 0. At `12:28:23Z` the independent `oap_hrm_candidate_startup_probe` = configured/reachable, read-only, no schema change and **write_performed:false**. These are startup candidate/selection CLASS proofs only, not selected provider hostname/DB/branch or independent commit/readback.
- Render SMI currently observed LIVE at `4839e40941ecdf48e982d9b91f567165f8d4be19` / `dep-dan7v90ae00c73dr528g`; the inactive older revision cannot be used as live proof. Separate Render PG provider listing `dpg-dahh4fss728c73b2sik0-a` remains available with 2026-10-10 expiry, but connector TLS handshake fails before SQL. **No backup archive has been produced or verified by this check.**

### Operator-only TLS read-only backup template (NOT run here)

Use an approved, separate trusted machine/workspace with current PostgreSQL client tools, an encrypted local volume, and **read-only** database credentials provisioned outside GitHub/chat. Define a private libpq `PGSERVICEFILE` with `[oap_hrm_readonly]` (the confirmed actual Render PG source only after provenance), `sslmode=require` plus verified host/certificate policy, and a separate `[oap_restore_offline]` service pointing **only at a disposable local Unix-socket PostgreSQL cluster** on a different isolated host. Use `PGPASSFILE` with strict file permissions; never paste URLs, passwords or private payloads into logs or GitHub. These shell examples are an **operator-reviewed template**, not execution proof:

```sh
set -eu
umask 077
archive_dir="${OAP_PRIVATE_RECOVERY_DIR:?private encrypted directory required}"
test -d "$archive_dir"
test ! -L "$archive_dir"
# The operator must separately verify pg_service.conf, certificate, read-only
# role, expected selected database, and offline restore target before commands.
pg_dump --dbname='service=oap_hrm_readonly' --format=custom \
  --no-owner --no-acl --file="$archive_dir/hrm-recovery.dump"
pg_restore --list "$archive_dir/hrm-recovery.dump" \
  > "$archive_dir/hrm-recovery.contents.private.txt"
(cd "$archive_dir" && sha256sum hrm-recovery.dump \
  > hrm-recovery.sha256.private.txt)
# Stop here unless an independently confirmed, isolated and disposable local
# PostgreSQL restore database is ready. Do NOT run pg_restore against Render or
# Neon; do NOT confuse pg_restore --list with actual data restoration.
```

Before any `pg_restore --dbname='service=oap_restore_offline'` command, the operator must independently check that the target's service uses a local Unix socket, `inet_server_addr() IS NULL`, `current_database()` equals the newly created unique **disposable** database, and no production credentials/network routes exist. Verify the offline restore contents and the exact new receipt ID/checksum in a new read-only connection after restoration. Retain only encrypted access-controlled archives; a custom-format dump is **NOT inherently encrypted**. Compare all relevant source schemas, stable IDs, digests and audit continuity with the restored target and retain a first-party receipt. A source access/TLS failure, archive-only result, or missing new-checkpoint readback keeps 25% RED.
