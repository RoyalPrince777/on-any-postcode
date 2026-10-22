# Eats order and payment integrity

This is a software contract for the existing Eats store and SIKA bridge. It
does not enable trading, capture, settlement or courier dispatch.

## Catalogue pricing

`POST /eats/orders` accepts a merchant, currency, fulfilment mode and a basket
of `{item_id, quantity}` objects. Item IDs are catalogue UUIDs; quantities are
JSON integers from 1 to 99. At most 100 distinct lines are accepted. Duplicate
IDs, extra item fields and coercions from booleans, floats or strings fail.

The store locks the active merchant and available menu items, verifies merchant
and currency agreement, calculates the total and persists names, unit prices,
quantities and currency as a snapshot. `amount_minor` is optional: when supplied,
it must be an integer matching the server total. It never sets the price. The
total must fit the existing PostgreSQL integer column.

The existing customer/idempotency-key identity is serialized in PostgreSQL.
An identical basket (independent of line order) returns its original snapshot,
timestamp and single creation event, even after the catalogue changes. A changed
merchant, basket, currency, fulfilment mode or quoted total conflicts. Repricing
requires a new order/key, not mutation of an accepted order.

## Explicit Eats payee contract

For this adapter, SIKA `payee_reference` must be the canonical `account_id` of
an open SIKA account owned by the order merchant's **current persisted owner at
binding time**. It is not a merchant UUID, arbitrary label, or a guessed external
beneficiary format. No general SIKA interpretation is changed.

The order, merchant, payer/payee accounts, intent and hold are locked during final
validation. Accounts are share-locked in ID order before the intent and hold;
the initial payee lookup is only a lock-order hint and is rechecked against the
locked intent. Payer and recipient currencies must match the order. The audit
event retains the merchant, recipient account, payment, hold and pricing version.
The store retains cross-order reuse denial and idempotent binding behavior.

## Migration and legacy records

The original Eats migration/checksum is unchanged. Explicit schema initialization
adds and records `0002_oap_eats_order_integrity`, with an advisory migration lock
and checksum mismatch rejection. It adds nullable `pricing_version` without
backfilling historical orders. Schema initialization is not a deployment receipt.

Only new catalogue-priced orders receive `eats_catalogue_v1`. Historical or
unknown-version orders cannot bind a payment or replay as verified orders. They
must be reviewed and replaced with a new correctly priced order/key; they are
never silently rewritten. Deployment must apply the migration before this code.

## Verification boundary

The existing isolated loopback PostgreSQL CI inventory verifies snapshots,
negative permissions, quote tampering, retries, concurrency, rollback, migration
and payee/account agreement. Seeded account/payment statuses are test data, not
provider authorization or financial receipts. The existing SIKA two-decimal
amount convention is retained; wider currency acceptance is not certified here.

Merchant/account onboarding, accepted trading/compliance scope, live payment
authority, operator availability, crash/power-loss recovery and a controlled
healthy routing host still need independent proof. Product VPI remains N/A.
