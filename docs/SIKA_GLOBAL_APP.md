# SIKA Global App

## Purpose
First-party SIKA application shell with one canonical value unit and a global currency quote boundary.

## Locked value model
- 1 SIKA = £1 GBP target anchor.
- One SIKA worldwide; no national forks of the unit.
- Any valid three-letter currency code can be quoted when an authorised SIKA Treasury GBP-per-unit rate is supplied.
- Browser/client code does not contact a bank or external FX provider.
- Rates are input to the first-party boundary; a later regulated treasury integration can authenticate and ingest them server-side.

## Current working surfaces
- `/sika` mobile-first application shell.
- `GET /api/sika/status` truthful capability status.
- `POST /api/sika/quote` read-only SIKA → local-currency quotation.
- Wallet, Exchange, Treasury and Market navigation anatomy.
- Pay, Card and Cash-out endpoints fail closed with HTTP 423.

## Explicitly not claimed
No deposit account, e-money issuance, bank licence, debit card, cash withdrawal, payment execution, foreign-exchange execution, safeguarding account or customer funds are live.

## Run
```bash
flask --app sika_global_app run --port 5011
```

## Test
```bash
pytest -q tests/test_sika_global_app.py
```

## Next regulated boundary
When authorised, connect a server-side SIKA Treasury rate-ingestion service and regulated settlement adapter. Keep provider-specific bank/payment credentials behind the server boundary so the SIKA app remains first-party.
