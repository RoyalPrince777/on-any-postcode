# SIKA Post Office — cash-access requirements and gap register

Status: FOUNDER DESIGN ONLY / FAIL CLOSED. This document names an OAP **proposed product**, not a partnership, licensed post office, Post Office Ltd affiliation, functioning cash office, or permission to take deposits.
Owner: Founder; must be read with SIKA_INSTALLABLE_MONEY_APP_CONTRACT.md and the existing four-stage protocol.

## What "OAP Post Office" means

A proposed OAP-owned, postcode-first **physical-service and cash-access layer** inside SIKA. Keep separate from the existing UK Post Office Ltd brand and facilities; do not imply an agreement with it. An OAP Spot is NOT an approved cash location just because it has a postcode.

A customer may discover verified service locations, request appointment-based services, see supported denominations and published fees, and receive a receipt. A real cash exchange requires authorised money handling, an operating location, trained accountable staff, appropriate security and insurance, authenticated cash, protected funds, secure transport, reconciliation and approved withdrawal/deposit rails.

SIKA is one account across OAP and the independent install. No duplicates, no public Founder data.

## Big gaps to close (each must have named owner, dependency, evidence, test and rollback)

| Gap | Minimum proof before offering to the public |
|---|---|
| Legal entity, regulatory perimeter | UK counsel determines bank / e-money / payment-service / agent status and cash handling authorisations; documented approval and permitted product descriptions |
| Use of "Post Office" name | Brand/trademark review and clear no-affiliation naming/disclosures |
| Account and access | Server-side individual ownership, identity verification, KYC/AML, sanctions, youth controls and complaints procedures; no automatic Founder/member authority |
| One installable SIKA app | Own manifest, start URL, icons, scope and non-cacheable financial pages; Android install test; OAP embedded entry hits the *same* account |
| Monetary issuance/redemption | Funded one-to-one monetary SIKA only after lawful issuance; redeem at par under compliant terms; insufficient funds and no credit |
| Recognition separation | Legacy SIKA credits remain non-money, no retroactive GBP conversion from points or engagement |
| Double-entry ledger | Integer pennies, immutable postings, idempotency, reconciliation, pending/posted/reversed transactions, dispute/refund and chargeback handling |
| Safeguarding and treasury | Customer funds separate from OAP revenue, liability reconciliation, documented bank/insurer/guarantee arrangements and operating liquidity |
| Notes and coins in | Verified deposit agent or controlled site, accepted denominations, counted/checked cash, two-person controls where appropriate, authenticity, deposit receipt, cash-in-transit, protected funds and delayed finality until cash accepted |
| Notes and coins out | Verified cash inventory, liquidity, identification and limits, withdrawal reservation/expiry, exact-once debit, dispense confirmation, partial/failure reversal and cash-drawer reconciliation |
| Card | Lawful issuer/network and processor arrangements, cardholder terms, provisioning/freeze, lost/stolen, authorisation, chargeback and PCI scope; never invent a card number |
| Payment rails | Actual supported card/bank options and fees/settlement; no false "no third parties" promises when mandatory rails exist |
| Physical security | Site safety, employee training, insurance, handling limits, CCTV/privacy evaluation, tamper controls, robbery/incident response and audit |
| Location directory | Only operator-verified sites with real services, accessibility, hours, denominations, fees, address, status and last-confirmed time; no fake map pins |
| Customer protection | Clear terms, redemption, failed payouts, disclosures about FSCS status, fraud reporting, help/complaints and closure |
| Privacy | No customer-data sales or ad telemetry; necessary regulated processing, data minimisation, retention and access receipts |
| Geographic Manifest | 7% of *optional* GBP Manifest amount only; named eligible recipient/treasury for selected area, and approved remaining-93% and fee allocations |
| Resilience | Outages, queue expiry, offline prohibition on cash credit, restore, reconciled cash counts, incident response and escrow/safeguarding controls |
| Operational proof | Contract tests, negative and concurrent transaction tests, supervised end-to-end cash deposit/withdrawal proof and signed approval |

## Approved future interaction (not enabled)

1. User chooses Notes & Coins or Cash Out, sees genuine locations, limits, fees and eligibility.
2. SIKA verifies identity, available monetary value, location and applicable authorised service.
3. Operator confirms physically received cash or cash dispensed, through audited dual-sided receipt.
4. Ledger settles exactly once only after the verified event, with exception-handling and customer receipt.
5. Reconcile cash inventory, protected funds, liabilities and operator settlement. Fail closed on mismatch.

Never credit a photographed banknote, a QR scan, an unverified staff assertion, a pending cash deposit, or a machine that has not confirmed receipt. Never dispense cash against recognition points or a pending unfunded balance. At no time treat customers' notes/coins as Founder's personal funds.

## Existing external-world constraints verified during design

- UK Post Office's Banking Framework covers services for participating banks; it does not automatically enable SIKA accounts. https://www.postoffice.co.uk/everydaybanking
- FCA e-money/payment institution authorisation and agent requirements: https://www.fca.org.uk/firms/apply-emoney-payment-institution/emi
- FCA safeguarding requirements, updated May 2026: https://www.fca.org.uk/firms/emi-payment-institutions-safeguarding-requirements
- FCA cash-based money laundering guidance: https://www.fca.org.uk/firms/financial-crime/money-laundering-terrorist-financing/cash-based-money-laundering

## Four gates remain unchanged

25% Recovery: audit existing SIKA routes, auth, install scope and ledgers; rights/permissions/perimeter and rollback evidence.
50% Runtime Guard: tests for quote and ledger maths, no debt, cash finality, duplicate/cancelled deposits, withdrawal failure, refund and no fabricated facilities.
75% Aegis Isolation: fraud, KYC/AML, privacy, employee/agent boundaries, cash inventory and safeguarded-funds reconciliation, recovery tests.
100% Green Gate + Founder Final: actual authorisations/operational arrangements; exact tested commit; physically verified service location; complete end-to-end proof; Founder final.

Until all gates pass, cash-in, cash-out, cards and monetary SIKA remain disabled with explicit unavailable status. No bank or Post Office affiliation claims.
