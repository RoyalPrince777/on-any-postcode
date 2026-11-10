# SIKA Global recovery slice

Recovered from the useful bounded core of stale PR #651 onto current main.

## Included

- Canonical SIKA unit.
- Founder target: **1 SIKA = 1 GBP**.
- Read-only quote engine using explicit treasury snapshots.
- Strict rejection of missing, non-positive and non-finite rates.
- Explicit release boundary for a later authorised payment/provider adapter.
- Provider-authority evidence and settlement receipt remain mandatory before
  regulated execution can be enabled.

## Not claimed

This slice does not accept deposits, hold customer funds, issue bank accounts,
issue cards, execute FX, cash out, or move money. A founder-supplied lawful
route can be integrated later as an adapter only after its authority scope,
provider identity, environment and receipt contract are evidenced.

## Recovery rule

Do not merge stale PR #651 wholesale. Recover reviewed capabilities in bounded,
current-main slices with exact-head CI evidence.
