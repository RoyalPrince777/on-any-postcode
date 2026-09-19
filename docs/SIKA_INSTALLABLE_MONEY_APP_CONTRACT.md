# SIKA Money app — Founder-governed implementation contract

Status: DESIGN / FAIL-CLOSED. No bank, e-money, card, cash or payout capability is certified by this document.
Owner: Human Founder. Upgrade-only: preserve existing OAP install shell, SIKA recognition store, OAP Pass, My Card, public/private separation and four-stage protocol.

## Product boundary

SIKA is one branded financial front door, installable separately and available inside OAP. Both entry points must address the **same authorised account**, not duplicate wallets. The existing public OAP PWA manifest is **not** evidence of a separately installable SIKA app. Independent installation requires its own scoped manifest, start URL, permitted service-worker scope, assets and verified installation on supported devices. Never cache financial responses, personal statements, tokens, Founder content or credentials in public/offline shells.

Proposed par value for a future monetary product: **1 SIKA Money = £1 GBP** only under approved funding, safeguarding, redemption, issuance and applicable permissions. SIKA Recognition remains non-monetary and cannot be converted to GBP merely through views, likes or activity. Do not silently reclassify existing SIKA points as money or overwrite the existing non-money product store.

## Screens (all real-money actions disabled until gate evidence)

- Home: actual available monetary balance when authorised; otherwise explicitly unavailable, not a fabricated £0 bank balance.
- Add Money: source, funds-confirmed receipt and reconciliation.
- Pay / Request: available payment methods, price, recipient, fees and total; no preselected optional extra.
- Cash Out: redemption to a verified permitted destination; insufficient-funds and refund handling.
- Card: card status and freeze controls only after genuine issuer integration; no invented card numbers.
- Notes & Coins: display operationally verified accepted deposit and cash-out sites; app alone cannot accept or dispense cash.
- Proof of Created Value: creation, rights, views, likes, commercial sale and monetary funding are separate evidence types.
- Manifest My World: optional Manifest More GBP amount; 7% of that **optional amount** allocates to an eligible named area recipient (postcode / borough / county-region / country / global). The remaining 93% and fees require approved written allocation rules.
- Control Center: privacy, permissions, limits, statements, audit, dispute and account closure.

## Non-negotiable ledger invariants

1. Double-entry, integer minor units and immutable audit entries; never floats for money.
2. Per-identity ownership and Founder-private separation, both enforced server-side.
3. No negative available balances, credit, overdrafts, loans or Pay Later.
4. At-most-once settlement with idempotency keys; replay and race tests.
5. Distinguish pending, confirmed, refunded, disputed, reversed and paid-out amounts.
6. Reconcile customer liabilities, protected funds, merchants/creators payable, area allocations and OAP-earned revenue.
7. Never mint cash SIKA from non-money recognition; no unfunded 1:1 conversion.
8. No automatic consequential action without required Human approval and lawful operational authority.
9. No sale of customer data or third-party advertising telemetry; limit legally/operationally necessary disclosures and never claim absolute zero external disclosure.
10. Fail closed if payment, issuer, safeguarding, entitlement, anti-fraud or lawful permission evidence is absent.

## Four-stage gate, no extra stages

- 25% Recovery: inspect existing SIKA routes, wallet schemas, OAP PWA and auth; retain rollback evidence; select legal funds flow and proof requirements.
- 50% Runtime Guard: unit/integration tests for par value, balances, total, refunds, no debt, replay/race/idempotency and no fake available features.
- 75% Aegis Isolation: identity isolation, auth, secret handling, fraud, outage/restore, cache exclusion, full reconciliation, cash-handling boundaries.
- 100% Green Gate + Founder Final: necessary permissions and arrangements verified, exact commit merged/deployed, installability proven, real end-to-end funded transaction and reconciliation receipts, Founder approval.

Nothing in this file deploys services, obtains permissions, issues a card, accepts deposits, issues SIKA Money or moves customer funds.