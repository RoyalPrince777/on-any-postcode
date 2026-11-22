# Local HQ and public service

The browser Bank Menu has six sections: My SIKA, Money & Payments, Cards & Banking,
Global SIKA, OAP Ecosystem, and Security & Support. All entries use existing routes.
The private Activity HTML page at `/pay/bank/me/transactions` reads the existing owner-scoped
activity projection; `/pay/bank/me/activity` remains the JSON API. No payment history or
balance is invented when the store is unavailable. Public menu links for private account
access point to HQ 5000. Locked services link to status pages, never execution controls.

| Service | Address | Purpose |
| --- | --- | --- |
| HQ | http://127.0.0.1:5000 | Existing signed-in account, My World, SIKA account and Founder controls |
| Public | http://127.0.0.1:5052 | Public World, Store and browser discovery |

Use the same complete checkout and existing account/database configuration. There is one
canonical account/ledger system. No account, balance or password is created by these commands.

Start each service through its normal process supervisor using:

```sh
python scripts/run_oap_local.py hq
python scripts/run_oap_local.py public
```

Each command runs in the foreground. Existing occupied ports must first be handled through
their existing supervisor; neither launcher kills, replaces or restarts another process.
Both bind to loopback. This is local operation, not a public internet/VPS deployment.
HQ authentication, Guardian/HRM, financial gates and Founder authority remain in force.

The process role is captured at startup through `OAP_LOCAL_SERVICE_ROLE`. Host, forwarded
port and gateway headers cannot change it. Public mode denies protected routes and internal
service paths before the views execute. Selected GET/HEAD account and sign-in doors hand
off to the fixed HQ address; account APIs and Founder operations return a no-store 404.
The two local roles use distinct Flask session cookie names. Existing sessions may need a
fresh sign-in. Browser ports alone do not isolate identity-provider cookies.

`python app.py` now starts loopback HQ on 5000 without the debugger. Explicitly setting
`OAP_LOCAL_SERVICE_ROLE=public` starts the public service on 5052 instead. Existing remote
deployments without a local role retain their current configuration.

## Verification and recovery

```sh
python scripts/check_sika_browser_5052.py
```

The legacy filename is retained, but the read-only checker now verifies public 5052 and
anonymous HQ authentication boundaries on 5000. It cannot certify a real Founder sign-in,
Redmi A5 behaviour, production deployment, signed installation, or release readiness.

`scripts/apply_sika_5052.py` is a legacy source-navigation adapter, not the service launcher.
It now accepts the current bank markup idempotently and still refuses missing or ambiguous
anchors before writing. Its limited file list does not install the service boundary; use
the complete reviewed revision for this split. It never provisions accounts, starts servers,
or moves money. Installation and financial execution remain evidence-gated.
