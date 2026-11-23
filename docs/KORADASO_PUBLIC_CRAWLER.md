# KORADASO public web crawler — controlled first-party foundation

Status: **manual bounded crawler implemented; global coverage NOT claimed**.

The crawler lives at `mission_control/koradaso_public_crawler.py` and
`scripts/koradaso_crawl_public.py`. It writes into the existing SQLite
public web index and requires a manually selected, reviewed HTTPS seed.

## Run only after authorising an eligible public domain

```bash
python scripts/koradaso_crawl_public.py \
  --seed https://example.org/ \
  --db "$HOME/koradaso-public.sqlite3" \
  --max-pages 3
```

Set `OAP_KORADASO_WEB_INDEX` to the same local database when deliberately
serving results with `/koradaso/web-search`. This is an illustrative command;
it is **not evidence that example.org was fetched or indexed**.

## Opt-in approved-site queue (source-only, not deployed)

The existing crawler now has a persistent bounded queue in
`mission_control/koradaso_crawl_fleet.py` and
`scripts/koradaso_fleet.py`. Nothing runs automatically on app startup,
Android startup or the VPS. An operator must explicitly approve each HTTPS
seed and invoke `run-once`; an external scheduler or service is **not**
installed. Queue state is separate from the public search index.

```bash
python scripts/koradaso_fleet.py --state "$HOME/koradaso-fleet.sqlite3" \
  --index "$HOME/koradaso-public.sqlite3" approve \
  --seed https://example.org/ --interval-hours 24
python scripts/koradaso_fleet.py --state "$HOME/koradaso-fleet.sqlite3" \
  --index "$HOME/koradaso-public.sqlite3" run-once
python scripts/koradaso_fleet.py --state "$HOME/koradaso-fleet.sqlite3" \
  --index "$HOME/koradaso-public.sqlite3" status
```

Commands are examples, not proof of a real crawl. At most one due seed is
claimed per invocation, with a 120-second transactional lease, daily minimum
interval, one-hour retry cooldown, and a maximum of 21 approved URLs.
Revoke with the `revoke --seed` subcommand; revocation prevents future
claims but does not cancel a crawl already in progress. The existing
robots.txt, public-DNS/TLS, per-crawl size and depth limits still apply.

Automated triggering, safe concurrency under process failure, per-host/global
rate limiting, deletion requests, real-world crawl volumes, and production
acceptance remain **Unknown**. Do not label this an autonomous fleet Green.

## Safety contract

- No crawler on Flask startup, Android launch, scheduled task or production; the new queue only acts on explicit CLI invocation.
- One approved public HTTPS host; no cross-host crawling.
- Only public DNS addresses; the connection is pinned to the validated IP,
  with TLS hostname verification. Do not trust DNS resolution alone.
- Never follow redirects, whether to another domain or another network.
- A real accessible robots policy is required; deny if unavailable or disallowed.
- At most five public HTML pages, one link depth, 256 KiB response limit,
  five-second connection timeout and at least one second between requests.
- `noindex` HTML meta means no indexing. No credentials, cookies, images,
  JavaScript execution, private pages, local network or onion access.
- Failed or blocked pages produce no fabricated search records.
- SMI and Guardian do not automatically turn crawling on; Founder-controlled
  operations, audit and allowlisting are required before widening scope.

## Not built / future gates

Global multi-domain scheduling, public crawl discovery, crawl-delay/backoff
policy, 404 robots handling, `X-Robots-Tag` headers, robots refresh, opt-out
and removal workflow, full-text extraction, canonical/duplicate handling,
relevance beyond metadata, hostile HTML robustness and content trust review
all remain engineering tasks. The current tool is not a production-ready
internet crawler and must not be presented as one.
