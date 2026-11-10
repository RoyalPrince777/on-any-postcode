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

## Safety contract

- No crawler on Flask startup, Android launch, scheduled task or production.
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
